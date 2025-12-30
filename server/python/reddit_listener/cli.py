"""
CLI Module
==========

Command-line interface for the Reddit Listener.
"""

import argparse
import time
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)
log = logging.getLogger(__name__)

from .config import validate_reddit_config, get_config_summary
from .store import create_source, delete_source, get_enabled_sources
from .scheduler import run_once, backfill_source


def main():
    parser = argparse.ArgumentParser(description="Reddit Listener CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # ─── run-once ─────────────────────────────────────────────────────────────
    cmd_run_once = subparsers.add_parser("run-once", help="Run a single ingest cycle")
    
    # ─── run ──────────────────────────────────────────────────────────────────
    cmd_run = subparsers.add_parser("run", help="Run the listener loop")
    cmd_run.add_argument("--interval-min", type=int, default=15, help="Interval in minutes")
    
    # ─── add-subreddit ────────────────────────────────────────────────────────
    cmd_add_sub = subparsers.add_parser("add-subreddit", help="Add a subreddit source")
    cmd_add_sub.add_argument("subreddit", help="Subreddit name (without r/)")
    cmd_add_sub.add_argument("--user-id", type=int, required=True, help="User ID")
    cmd_add_sub.add_argument("--group-id", type=int, help="Group ID (optional)")
    
    # ─── add-query ────────────────────────────────────────────────────────────
    cmd_add_query = subparsers.add_parser("add-query", help="Add a keyword query source")
    cmd_add_query.add_argument("query", help="Search query")
    cmd_add_query.add_argument("--subreddit", help="Limit to subreddit (optional)")
    cmd_add_query.add_argument("--user-id", type=int, required=True, help="User ID")
    cmd_add_query.add_argument("--group-id", type=int, help="Group ID (optional)")
    
    # ─── backfill ─────────────────────────────────────────────────────────────
    cmd_backfill = subparsers.add_parser("backfill", help="Backfill historical posts")
    cmd_backfill.add_argument("--source-id", type=int, required=True, help="Source ID to backfill")
    cmd_backfill.add_argument("--hours", type=int, default=72, help="Hours to go back")
    
    # ─── cleanup ──────────────────────────────────────────────────────────────
    cmd_cleanup = subparsers.add_parser("cleanup", help="Delete a source and its data")
    cmd_cleanup.add_argument("--source-id", type=int, required=True, help="Source ID to delete")
    cmd_cleanup.add_argument("--user-id", type=int, help="User ID for verification")
    
    # ─── reprocess-cards ──────────────────────────────────────────────────────
    cmd_reprocess = subparsers.add_parser("reprocess-cards", help="Extract strategy cards from existing items")
    cmd_reprocess.add_argument("--limit", type=int, default=50, help="Max items to process")
    
    # ─── config ──────────────────────────────────────────────────────────────
    subparsers.add_parser("config", help="Show configuration summary")

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
        
    # Validate config for run commands
    if args.command in ("run", "run-once", "backfill", "reprocess-cards"):
        errors = validate_reddit_config()
        if errors:
            log.error("Configuration errors:")
            for e in errors:
                log.error(f"- {e}")
            sys.exit(1)

    if args.command == "run-once":
        run_once()
        
    elif args.command == "run":
        log.info(f"Starting runner loop (interval: {args.interval_min} min)")
        while True:
            try:
                run_once()
            except Exception as e:
                log.error(f"Run exception: {e}", exc_info=True)
            
            log.info(f"Sleeping for {args.interval_min} minutes...")
            time.sleep(args.interval_min * 60)
            
    elif args.command == "add-subreddit":
        try:
            sid = create_source(
                user_id=args.user_id,
                group_id=args.group_id,
                source_type="subreddit",
                value=args.subreddit
            )
            log.info(f"Added source ID {sid}")
        except Exception as e:
            log.error(f"Failed to add source: {e}")
            sys.exit(1)
            
    elif args.command == "add-query":
        try:
            sid = create_source(
                user_id=args.user_id,
                group_id=args.group_id,
                source_type="keyword",
                value=args.query,
                subreddit=args.subreddit
            )
            log.info(f"Added source ID {sid}")
        except Exception as e:
            log.error(f"Failed to add source: {e}")
            sys.exit(1)
            
    elif args.command == "backfill":
        backfill_source(args.source_id, args.hours)
        
    elif args.command == "cleanup":
        if delete_source(args.source_id, args.user_id):
            log.info(f"Deleted source {args.source_id}")
        else:
            log.error(f"Failed to delete source {args.source_id} (not found or user mismatch)")
            
    elif args.command == "reprocess-cards":
        reprocess_strategy_cards(args.limit)
            
    elif args.command == "config":
        import json
        print(json.dumps(get_config_summary(), indent=2))


def reprocess_strategy_cards(limit: int = 50):
    """Extract strategy cards from existing items that don't have one."""
    from .store import get_items_without_cards, insert_strategy_card
    from .extractor import extract_strategy_card, enforce_evidence_limits
    from .normalize import normalize_text
    
    log.info(f"Reprocessing up to {limit} items for strategy card extraction...")
    
    items = get_items_without_cards(limit)
    log.info(f"Found {len(items)} items without strategy cards")
    
    extracted = 0
    for item in items:
        log.info(f"Processing item {item['id']}: {item['title'][:50]}...")
        
        # Normalize title and body
        norm_title, _, _ = normalize_text(item['title'] or "", strip_markdown=True)
        norm_body, _, _ = normalize_text(item['body'] or "", strip_markdown=True)
        
        # Extract card
        card = extract_strategy_card(
            title=norm_title,
            body=norm_body,
            top_comments=[],  # We don't have comments handy for reprocessing
            permalink=item['external_url']
        )
        
        if card:
            card = enforce_evidence_limits(card)
            try:
                insert_strategy_card(
                    item_id=item['id'],
                    platform_targets=card.get('platform_targets', []),
                    niche=card.get('niche', 'general'),
                    tactic=card['tactic'],
                    steps=card.get('steps', []),
                    preconditions=card.get('preconditions', {}),
                    metrics=card.get('metrics', {}),
                    risks=card.get('risks', []),
                    confidence=card['confidence'],
                    evidence=card.get('evidence', {})
                )
                extracted += 1
                log.info(f"  ✓ Extracted: {card['tactic'][:50]}...")
            except Exception as e:
                log.error(f"  ✗ Failed to save card: {e}")
        else:
            log.info(f"  - No strategy found")
            
    log.info(f"Reprocessing complete: {extracted}/{len(items)} cards extracted")


if __name__ == "__main__":
    main()

