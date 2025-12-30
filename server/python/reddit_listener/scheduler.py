"""
Scheduler Module
================

Job loop for the Reddit Listener.
Orchestrates fetching, normalizing, scoring, chunking, and spike detection.
"""

import time
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from .config import (
    SPIKE_FACTOR_THRESHOLD,
    DEFAULT_FETCH_LIMIT,
    COMMENTS_FETCH_LIMIT,
    COMMENTS_DEPTH,
    CHUNK_MIN_CHARS,
)
from .reddit_api import get_client
from .normalize import normalize_text
from .quality import compute_quality_score, passes_quality_filter, is_high_quality
from .store import (
    create_source,
    get_enabled_sources,
    update_listener_state,
    get_listener_state,
    upsert_item,
    upsert_comment,
    insert_chunk,
    insert_strategy_card,
    insert_alert,
    count_items_in_window,
    get_top_items_in_window,
)
from .chunker import create_chunks, build_metadata_header
from .extractor import extract_strategy_card, enforce_evidence_limits

log = logging.getLogger(__name__)

# Minimum items required to trigger a spike alert (to avoid noise on low volume)
MIN_SPIKE_COUNT = 10


def run_once(force_source_id: Optional[int] = None):
    """
    Run one iteration of the listener loop.
    
    Args:
        force_source_id: Only run a specific source ID
    """
    log.info("Starting listener run")
    client = get_client()
    
    sources = get_enabled_sources()
    if force_source_id:
        sources = [s for s in sources if s['id'] == force_source_id]
    
    log.info(f"Processing {len(sources)} sources")
    
    for source in sources:
        try:
            process_source(client, source)
        except Exception as e:
            log.error(f"Error processing source {source['id']} ({source['value']}): {e}", exc_info=True)
            
    log.info("Listener run completed")


def process_source(client, source: dict):
    """
    Process a single source: fetch, ingest, chunk, extract, check spikes.
    """
    source_id = source['id']
    source_type = source['type']
    value = source['value']
    subreddit = source['subreddit']
    
    log.info(f"Processing source {source_id}: {source_type}={value} " + 
             (f"(sub={subreddit})" if subreddit else ""))
    
    # Get state
    state = get_listener_state(source_id)
    last_seen_utc = state['last_seen_created_utc'] if state else None
    
    # Fetch items
    if source_type == 'subreddit':
        items_gen = client.fetch_subreddit_new(
            subreddit=value,
            limit=DEFAULT_FETCH_LIMIT,
            last_seen_utc=last_seen_utc
        )
    else:  # keyword
        items_gen = client.fetch_search(
            query=value,
            subreddit=subreddit,
            limit=DEFAULT_FETCH_LIMIT,
            last_seen_utc=last_seen_utc
        )
    
    new_items_count = 0
    max_created_utc = last_seen_utc
    
    for item in items_gen:
        new_items_count += 1
        created_utc = item['created_utc']
        
        # Track max timestamp for state update
        if max_created_utc is None or created_utc > max_created_utc:
            max_created_utc = created_utc
            
        # 1. Normalize
        norm_title, _, _ = normalize_text(item['title'], strip_markdown=True)
        norm_body, is_removed, is_deleted = normalize_text(
            item['body'], 
            author=item['author'],
            strip_markdown=True
        )
        
        # 2. Score
        q_score = compute_quality_score(
            score=item['score'],
            num_comments=item['num_comments'],
            created_utc=created_utc,
            author_flair=item['author_flair'],
            nsfw=item['nsfw'],
            removed=is_removed or item['removed']
        )
        
        item['quality_score'] = q_score
        
        # 3. Store if passes filter
        if passes_quality_filter(
            score=item['score'],
            num_comments=item['num_comments'],
            created_utc=created_utc,
            quality_score=q_score,
            removed=item['removed']
        ):
            item_id = upsert_item(
                source_id=source_id,
                external_id=item['external_id'],
                external_url=item['external_url'],
                subreddit=item['subreddit'],
                title=item['title'],  # Store original
                body=item['body'],    # Store original
                author=item['author'],
                author_flair=item['author_flair'],
                score=item['score'],
                num_comments=item['num_comments'],
                created_utc=created_utc,
                quality_score=q_score,
                nsfw=item['nsfw'],
                removed=item['removed'],
                raw_json=item['raw_json']
            )
            
            # 4. Chunking (RAG)
            header = build_metadata_header(
                subreddit=item['subreddit'],
                score=item['score'],
                created_utc=created_utc.isoformat(),
                url=item['external_url'],
                title=norm_title
            )
            
            # Combine title + body for chunking
            full_text = f"{norm_title}\n\n{norm_body}"
            chunks = create_chunks(full_text, header)
            
            for chunk_text, chunk_hash in chunks:
                insert_chunk(item_id, chunk_text, chunk_hash)
            
            # 5. Fetch comments if high quality
            top_comments_text = []
            if is_high_quality(q_score):
                log.debug(f"Fetching comments for high-quality item {item['external_id']}")
                comments = client.fetch_comments_for_submission(
                    submission_id=item['external_id'],
                    limit=COMMENTS_FETCH_LIMIT,
                    depth=COMMENTS_DEPTH
                )
                
                for comm in comments:
                    c_norm, c_rem, c_del = normalize_text(comm['body'], comm['author'])
                    if not (c_rem or c_del):
                        top_comments_text.append(c_norm)
                        
                        c_id = upsert_comment(
                            item_id=item_id,
                            external_id=comm['external_id'],
                            parent_external_id=comm['parent_external_id'],
                            body=comm['body'],
                            author=comm['author'],
                            author_flair=comm['author_flair'],
                            score=comm['score'],
                            created_utc=comm['created_utc'],
                            removed=comm['removed'],
                            raw_json=comm['raw_json']
                        )
                        
                        # Chunk long comments
                        if len(c_norm) > CHUNK_MIN_CHARS:
                            comm_header = build_metadata_header(
                                subreddit=item['subreddit'],
                                score=comm['score'],
                                created_utc=comm['created_utc'].isoformat(),
                                url=item['external_url'], # Comments link to post usually
                                title=f"Comment on: {norm_title}"
                            )
                            c_chunks = create_chunks(c_norm, comm_header)
                            for ct, ch in c_chunks:
                                insert_chunk(item_id, ct, ch, comment_id=c_id)

            # 6. Extract Strategy Card
            card = extract_strategy_card(
                title=norm_title,
                body=norm_body,
                top_comments=top_comments_text,
                permalink=item['external_url']
            )
            
            if card:
                card = enforce_evidence_limits(card)
                insert_strategy_card(
                    item_id=item_id,
                    platform_targets=card['platform_targets'],
                    niche=card.get('niche', 'general'),
                    tactic=card['tactic'],
                    steps=card['steps'],
                    preconditions=card.get('preconditions', {}),
                    metrics=card.get('metrics', {}),
                    risks=card.get('risks', []),
                    confidence=card['confidence'],
                    evidence=card.get('evidence', {})
                )

    # Update state
    if max_created_utc:
        update_listener_state(source_id, max_created_utc)
        
    # 7. Spike Detection
    check_for_spikes(source_id)
    
    return new_items_count


def check_for_spikes(source_id: int):
    """
    Detect volume spikes: compares last 24h vs previous 24h.
    
    Triggers alert if:
    - factor >= SPIKE_FACTOR_THRESHOLD (default 2.0)
    - current_value >= MIN_SPIKE_COUNT (default 10)
    """
    now = datetime.now(timezone.utc)
    one_day = timedelta(days=1)
    
    window_current_start = now - one_day
    window_current_end = now
    
    window_prev_start = now - (one_day * 2)
    window_prev_end = window_current_start
    
    current_count = count_items_in_window(source_id, window_current_start, window_current_end)
    prev_count = count_items_in_window(source_id, window_prev_start, window_prev_end)
    
    # Avoid division by zero
    if prev_count == 0:
        factor = float(current_count) if current_count > 0 else 0.0
    else:
        factor = current_count / prev_count
        
    if factor >= SPIKE_FACTOR_THRESHOLD and current_count >= MIN_SPIKE_COUNT:
        log.warning(f"Spike detected for source {source_id}: factor={factor:.2f}, count={current_count}")
        
        # Get top items explaining the spike
        top_items = get_top_items_in_window(source_id, window_current_start, window_current_end, limit=5)
        
        insert_alert(
            source_id=source_id,
            window_start=window_current_start,
            window_end=window_current_end,
            metric='item_volume_24h',
            current_value=float(current_count),
            previous_value=float(prev_count),
            factor=factor,
            top_item_ids=top_items
        )


def backfill_source(source_id: int, hours: int = 72):
    """
    Backfill a source by fetching deeper history.
    
    Args:
        source_id: Source ID to backfill
        hours: How many hours back to go
    """
    log.info(f"Starting backfill for source {source_id} ({hours} hours)")
    client = get_client()
    
    # Get the source details
    sources = get_enabled_sources()
    source = next((s for s in sources if s['id'] == source_id), None)
    
    if not source:
        log.error(f"Source {source_id} not found or disabled")
        return

    # Calculate cutoff time
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    # Temporarily override fetch limit to go deep
    # We'll use a larger limit but rely on PRAW to verify timestamps
    # PRAW listings are generators, so we can iterate until we hit the cutoff
    DEEP_FETCH_LIMIT = 1000 
    
    source_type = source['type']
    value = source['value']
    subreddit = source['subreddit']
    
    if source_type == 'subreddit':
        items_gen = client.fetch_subreddit_new(
            subreddit=value,
            limit=DEEP_FETCH_LIMIT,
        )
    else:
        items_gen = client.fetch_search(
            query=value,
            subreddit=subreddit,
            limit=DEEP_FETCH_LIMIT,
        )
        
    count = 0
    for item in items_gen:
        created_utc = item['created_utc']
        if created_utc < cutoff_time:
            log.info(f"Reached cutoff time {cutoff_time} for backfill")
            break
            
        # Process item (reuse logic from process_source mostly, but simplified)
        # We duplicate key logic here to avoid complex state tracking updates during backfill
        
        # 1. Normalize
        norm_title, _, _ = normalize_text(item['title'], strip_markdown=True)
        norm_body, is_removed, is_deleted = normalize_text(
            item['body'], 
            author=item['author'],
            strip_markdown=True
        )
        
        # 2. Score
        q_score = compute_quality_score(
            score=item['score'],
            num_comments=item['num_comments'],
            created_utc=created_utc,
            author_flair=item['author_flair'],
            nsfw=item['nsfw'],
            removed=is_removed or item['removed']
        )
        
        # 3. Store if passes filter
        if passes_quality_filter(
            score=item['score'],
            num_comments=item['num_comments'],
            created_utc=created_utc,
            quality_score=q_score,
            removed=item['removed']
        ):
            upsert_item(
                source_id=source_id,
                external_id=item['external_id'],
                external_url=item['external_url'],
                subreddit=item['subreddit'],
                title=item['title'],
                body=item['body'],
                author=item['author'],
                author_flair=item['author_flair'],
                score=item['score'],
                num_comments=item['num_comments'],
                created_utc=created_utc,
                quality_score=q_score,
                nsfw=item['nsfw'],
                removed=item['removed'],
                raw_json=item['raw_json']
            )
            count += 1
            
    log.info(f"Backfilled {count} items for source {source_id}")
