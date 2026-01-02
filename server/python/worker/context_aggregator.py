"""
Context Aggregator
==================

Aggregates all available data sources for AI content generation.
Enforces tenant isolation and data caps for optimal token usage.

Data Sources:
    1. Game Context - Title, genre, tone, audience
    2. Document Chunks - RAG from uploaded PDFs  
    3. Competitor Data - Top hooks, hashtags, engagement
    4. Reddit Strategy Cards - Proven tactics
    5. Reddit Trends - Recent hot topics1

Author: ProjectMonopoly Team
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

import psycopg

from .config import DATABASE_URL

log = logging.getLogger(__name__)

# Data caps to prevent token explosion
DATA_CAPS = {
    "doc_chunks": 3,
    "competitor_hooks": 3,
    "competitor_hashtags": 5,
    "strategy_cards": 2,
    "reddit_trends": 3,
    "viral_hooks": 5,  # High-impact outlier hooks from viral_outliers
}


@dataclass
class ContentContext:
    """Aggregated context for AI content generation."""
    
    # Game info (required)
    game_title: str = ""
    genre: str = ""
    tone: str = ""
    audience: str = ""
    key_mechanics: str = ""
    
    # Documents (RAG)
    doc_chunks: List[str] = field(default_factory=list)
    
    # Competitors
    top_hooks: List[str] = field(default_factory=list)
    top_hashtags: List[str] = field(default_factory=list)
    competitor_handles: List[str] = field(default_factory=list)
    best_posting_day: str = "Wednesday"
    avg_engagement: float = 0.0
    
    # Reddit
    strategy_cards: List[Dict[str, Any]] = field(default_factory=list)
    trending_topics: List[str] = field(default_factory=list)
    
    # Viral Content (from outlier detection - optional)
    viral_hooks: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    has_data: bool = False
    confidence: str = "low"


def aggregate_context(
    user_id: int, 
    group_id: int, 
    platform: str = "instagram"
) -> ContentContext:
    """
    Fetch all available context for content generation.
    
    All queries are tenant-scoped to prevent cross-user data leakage.
    
    Args:
        user_id: Owner user ID
        group_id: Group ID for context
        platform: Target platform (instagram, tiktok)
        
    Returns:
        ContentContext with all available data
    """
    ctx = ContentContext()
    
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # 1. Game Context (required, scoped by user_id + group_id)
                ctx = _fetch_game_context(cur, user_id, group_id, ctx)
                
                # 2. Document Chunks (RAG, scoped by group_id)
                ctx = _fetch_doc_chunks(cur, group_id, platform, ctx)
                
                # 3. Competitor Data (scoped by user_id + group_id)
                ctx = _fetch_competitor_data(cur, user_id, group_id, ctx)
                
                # 4. Reddit Strategy Cards (scoped by user_id + group_id)
                ctx = _fetch_strategy_cards(cur, user_id, group_id, ctx)
                
                # 5. Reddit Trends (scoped by user_id + group_id)
                ctx = _fetch_reddit_trends(cur, user_id, group_id, ctx)
                
                # 6. Viral Hooks (optional - from outlier detection system)
                ctx = _fetch_viral_hooks(cur, user_id, group_id, platform, ctx)
                
                # Determine overall confidence
                ctx.has_data = bool(ctx.game_title)
                ctx.confidence = _determine_confidence(ctx)
                
    except Exception as e:
        log.exception("Failed to aggregate context: %s", e)
    
    log.info(
        "Context aggregated: game=%s, docs=%d, hooks=%d, viral=%d, cards=%d, confidence=%s",
        ctx.game_title[:30] if ctx.game_title else "N/A",
        len(ctx.doc_chunks),
        len(ctx.top_hooks),
        len(ctx.viral_hooks),
        len(ctx.strategy_cards),
        ctx.confidence
    )
    
    return ctx


def _fetch_game_context(
    cur, 
    user_id: int, 
    group_id: int, 
    ctx: ContentContext
) -> ContentContext:
    """Fetch game context (tenant-scoped)."""
    cur.execute("""
        SELECT game_title, primary_genre, tone, intended_audience, key_mechanics
        FROM game_contexts
        WHERE user_id = %s AND group_id = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (user_id, group_id))
    
    row = cur.fetchone()
    if row:
        ctx.game_title = row[0] or ""
        ctx.genre = row[1] or ""
        ctx.tone = row[2] or ""
        ctx.audience = row[3] or ""
        ctx.key_mechanics = row[4] or ""
        log.debug("Game context found: %s", ctx.game_title)
    else:
        log.warning("No game context for user=%d group=%d", user_id, group_id)
    
    return ctx


def _fetch_doc_chunks(
    cur, 
    group_id: int, 
    platform: str, 
    ctx: ContentContext
) -> ContentContext:
    """Fetch relevant document chunks via FTS (tenant-scoped)."""
    cap = DATA_CAPS["doc_chunks"]
    
    # Search for platform-relevant content
    search_terms = f"{platform} marketing social media content"
    
    cur.execute("""
        SELECT c.content
        FROM workshop_chunks c
        JOIN workshop_documents d ON c.document_id = d.id
        WHERE d.group_id = %s AND d.status = 'ready'
        ORDER BY ts_rank(c.tsv, plainto_tsquery('english', %s)) DESC
        LIMIT %s
    """, (group_id, search_terms, cap))
    
    rows = cur.fetchall()
    ctx.doc_chunks = [row[0] for row in rows if row[0]]
    
    if ctx.doc_chunks:
        log.debug("Fetched %d doc chunks for group=%d", len(ctx.doc_chunks), group_id)
    
    return ctx


def _fetch_competitor_data(
    cur, 
    user_id: int, 
    group_id: int, 
    ctx: ContentContext
) -> ContentContext:
    """Fetch competitor hooks, hashtags, and engagement (tenant-scoped)."""
    hook_cap = DATA_CAPS["competitor_hooks"]
    hashtag_cap = DATA_CAPS["competitor_hashtags"]
    
    # Top performing hooks (last 14 days)
    cur.execute("""
        SELECT cp.content, cpf.handle, (cp.engagement->>'likes')::int as likes
        FROM competitor_posts cp
        JOIN competitor_profiles cpf ON cp.profile_id = cpf.id
        JOIN user_competitors uc ON cpf.competitor_id = uc.competitor_id
        WHERE uc.user_id = %s 
          AND uc.group_id = %s
          AND cp.posted_at > NOW() - INTERVAL '14 days'
          AND cp.content IS NOT NULL
        ORDER BY likes DESC NULLS LAST
        LIMIT %s
    """, (user_id, group_id, hook_cap))
    
    rows = cur.fetchall()
    ctx.top_hooks = []
    ctx.competitor_handles = set()
    total_likes = 0
    
    for row in rows:
        content, handle, likes = row
        if content:
            # Extract first line as hook
            hook = content.split('\n')[0][:150]
            ctx.top_hooks.append(hook)
        if handle:
            ctx.competitor_handles.add(handle.lower())
        if likes:
            total_likes += likes
    
    ctx.competitor_handles = list(ctx.competitor_handles)
    ctx.avg_engagement = total_likes / max(len(rows), 1)
    
    # Top hashtags (frequency-based, last 14 days)
    cur.execute("""
        SELECT unnest(cp.hashtags) as tag, COUNT(*) as freq
        FROM competitor_posts cp
        JOIN competitor_profiles cpf ON cp.profile_id = cpf.id
        JOIN user_competitors uc ON cpf.competitor_id = uc.competitor_id
        WHERE uc.user_id = %s 
          AND uc.group_id = %s
          AND cp.posted_at > NOW() - INTERVAL '14 days'
        GROUP BY tag
        ORDER BY freq DESC
        LIMIT %s
    """, (user_id, group_id, hashtag_cap))
    
    rows = cur.fetchall()
    ctx.top_hashtags = [row[0] for row in rows if row[0]]
    
    # Best posting day
    cur.execute("""
        SELECT EXTRACT(DOW FROM cp.posted_at)::int as dow, 
               AVG((cp.engagement->>'likes')::int) as avg_likes,
               COUNT(*) as sample
        FROM competitor_posts cp
        JOIN competitor_profiles cpf ON cp.profile_id = cpf.id
        JOIN user_competitors uc ON cpf.competitor_id = uc.competitor_id
        WHERE uc.user_id = %s 
          AND uc.group_id = %s
          AND cp.posted_at > NOW() - INTERVAL '28 days'
        GROUP BY dow
        ORDER BY avg_likes DESC NULLS LAST
        LIMIT 1
    """, (user_id, group_id))
    
    row = cur.fetchone()
    if row:
        dow_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        ctx.best_posting_day = dow_names[row[0]] if row[0] is not None else "Wednesday"
    
    log.debug(
        "Competitor data: %d hooks, %d hashtags, best_day=%s",
        len(ctx.top_hooks), len(ctx.top_hashtags), ctx.best_posting_day
    )
    
    return ctx


def _fetch_strategy_cards(
    cur, 
    user_id: int, 
    group_id: int, 
    ctx: ContentContext
) -> ContentContext:
    """Fetch high-confidence Reddit strategy cards (tenant-scoped)."""
    cap = DATA_CAPS["strategy_cards"]
    
    cur.execute("""
        SELECT sc.tactic, sc.steps, sc.confidence
        FROM strategy_cards sc
        JOIN reddit_items ri ON sc.item_id = ri.id
        JOIN reddit_sources rs ON ri.source_id = rs.id
        WHERE rs.user_id = %s 
          AND rs.group_id = %s
          AND sc.confidence >= 0.7
        ORDER BY sc.confidence DESC, sc.created_at DESC
        LIMIT %s
    """, (user_id, group_id, cap))
    
    rows = cur.fetchall()
    ctx.strategy_cards = []
    
    for row in rows:
        tactic, steps, confidence = row
        if tactic:
            card = {
                "tactic": tactic,
                "steps": steps if steps else "",
                "confidence": float(confidence) if confidence else 0.0
            }
            ctx.strategy_cards.append(card)
    
    log.debug("Fetched %d strategy cards", len(ctx.strategy_cards))
    
    return ctx


def _fetch_reddit_trends(
    cur, 
    user_id: int, 
    group_id: int, 
    ctx: ContentContext
) -> ContentContext:
    """Fetch recent hot Reddit topics (tenant-scoped)."""
    cap = DATA_CAPS["reddit_trends"]
    
    cur.execute("""
        SELECT ri.title, ri.score
        FROM reddit_items ri
        JOIN reddit_sources rs ON ri.source_id = rs.id
        WHERE rs.user_id = %s 
          AND rs.group_id = %s
          AND ri.created_utc > NOW() - INTERVAL '7 days'
        ORDER BY ri.score DESC
        LIMIT %s
    """, (user_id, group_id, cap))
    
    rows = cur.fetchall()
    ctx.trending_topics = [row[0] for row in rows if row[0]]
    
    log.debug("Fetched %d trending topics", len(ctx.trending_topics))
    
    return ctx


def _determine_confidence(ctx: ContentContext) -> str:
    """Determine overall data confidence level."""
    score = 0
    
    if ctx.game_title:
        score += 2
    if ctx.doc_chunks:
        score += 1
    if len(ctx.top_hooks) >= 2:
        score += 2
    if ctx.strategy_cards:
        score += 1
    
    # Viral hooks boost confidence
    if ctx.viral_hooks:
        score += 2
    
    if score >= 5:
        return "high"
    elif score >= 3:
        return "medium"
    else:
        return "low"


def _fetch_viral_hooks(
    cur, 
    user_id: int, 
    group_id: int, 
    platform: str,
    ctx: ContentContext
) -> ContentContext:
    """
    Fetch viral outlier hooks (from viral_outliers table).
    
    GLOBAL NICHE BRAIN LOGIC:
    - If the current group has a defining 'genre' (e.g. 'Gaming'), we fetch
      viral outliers found by *ANY* user/group in the same genre.
    - If no genre match, we fall back to standard tenant isolation logic.
    """
    cap = DATA_CAPS["viral_hooks"]
    
    try:
        # Check if table exists first (for graceful degradation)
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'viral_outliers'
            )
        """)
        if not cur.fetchone()[0]:
            log.debug("viral_outliers table not found, skipping viral hooks")
            return ctx
        
        # ─────────────────────────────────────────────────────────────────
        # STRATEGY 1: GLOBAL NICHE SEARCH (Cross-Group Sharing)
        # ─────────────────────────────────────────────────────────────────
        if ctx.genre:
            log.info(f"🧠 Attempting Global Niche Search for genre: '{ctx.genre}'")
            
            # NOTE: usage of ILIKE for fuzzy genre matching
            # This query pulls outliers from competitors tracked by ANYONE
            # whose group context shares the same 'primary_genre'
            cur.execute("""
                WITH niche_groups AS (
                    SELECT group_id 
                    FROM game_contexts 
                    WHERE primary_genre ILIKE %s
                ),
                niche_competitors AS (
                    SELECT DISTINCT uc.competitor_id 
                    FROM user_competitors uc
                    JOIN niche_groups ng ON uc.group_id = ng.group_id
                )
                SELECT 
                    vo.hook,
                    vo.username,
                    vo.platform,
                    vo.multiplier,
                    vo.actual_engagement,
                    vo.support_count
                FROM viral_outliers vo
                JOIN competitor_profiles cp ON vo.username = cp.handle AND vo.platform = cp.platform
                JOIN niche_competitors nc ON cp.competitor_id = nc.competitor_id
                WHERE vo.platform = %s
                  AND vo.expires_at > (NOW() AT TIME ZONE 'UTC')
                  AND vo.multiplier >= 10  -- High quality only
                ORDER BY vo.multiplier DESC, vo.actual_engagement DESC
                LIMIT %s
            """, (f"%{ctx.genre}%", platform, cap))
            
            rows = cur.fetchall()
            
            if rows:
                log.info(f"   → Found {len(rows)} global niche viral hooks!")
                _populate_viral_hooks(ctx, rows)
                return ctx
            else:
                log.info("   → No global niche data found, falling back to local...")

        # ─────────────────────────────────────────────────────────────────
        # STRATEGY 2: LOCAL FALLBACK (Tenant Scoped)
        # ─────────────────────────────────────────────────────────────────
        # Fallback to outliers from strictly your OWN tracked competitors
        cur.execute("""
            SELECT 
                vo.hook,
                vo.username,
                vo.platform,
                vo.multiplier,
                vo.actual_engagement,
                vo.support_count
            FROM viral_outliers vo
            JOIN competitor_profiles cp ON vo.username = cp.handle AND vo.platform = cp.platform
            JOIN user_competitors uc ON cp.competitor_id = uc.competitor_id
            WHERE uc.user_id = %s
              AND uc.group_id = %s 
              AND vo.platform = %s
              AND vo.expires_at > (NOW() AT TIME ZONE 'UTC')
              AND vo.multiplier >= 10
            ORDER BY vo.multiplier DESC, vo.actual_engagement DESC
            LIMIT %s
        """, (user_id, group_id, platform, cap))
        
        rows = cur.fetchall()
        _populate_viral_hooks(ctx, rows)
        
        if ctx.viral_hooks:
            log.debug(
                "Fetched %d local viral hooks (top multiplier: %dx)",
                len(ctx.viral_hooks),
                ctx.viral_hooks[0]["multiplier"] if ctx.viral_hooks else 0
            )
    
    except Exception as e:
        # Graceful degradation - don't fail if viral module isn't ready
        log.warning("Could not fetch viral hooks: %s", e)
    
    return ctx

def _populate_viral_hooks(ctx: ContentContext, rows: List[Any]) -> None:
    """Helper to populate the context list from DB rows."""
    ctx.viral_hooks = []
    for row in rows:
        hook, username, plat, multiplier, engagement, support = row
        if hook:
            ctx.viral_hooks.append({
                "hook": hook[:280],
                "username": username or "unknown",
                "multiplier": multiplier,
                "engagement": engagement,
                "support_count": support,
            })
