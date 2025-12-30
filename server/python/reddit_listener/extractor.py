"""
Strategy Card Extractor
=======================

Extracts structured marketing strategy cards from Reddit content.
Uses LLM if available, otherwise returns None.
"""

import json
import logging
import requests
from typing import Optional, Dict, Any

from .config import LLM_ENABLED, LLM_PROVIDER, OLLAMA_HOST, OLLAMA_MODEL
from .normalize import truncate_text

log = logging.getLogger(__name__)

# Schema for Strategy Card
STRATEGY_CARD_SCHEMA = {
    "type": "object",
    "properties": {
        "platform_targets": {"type": "array", "items": {"type": "string"}},
        "niche": {"type": "string"},
        "tactic": {"type": "string"},
        "steps": {
            "type": "array", 
            "items": {
                "type": "object", 
                "properties": {"step": {"type": "integer"}, "action": {"type": "string"}}
            }
        },
        "preconditions": {"type": "object"},
        "metrics": {"type": "object"},
        "risks": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number"},
        "evidence": {
            "type": "object",
            "properties": {
                "quote_snippets": {"type": "array", "items": {"type": "string"}},
                "permalink": {"type": "string"}
            }
        }
    },
    "required": ["platform_targets", "tactic", "steps", "confidence"]
}

EXTRACTION_PROMPT = """You are a strategy analyst for indie game developers. Analyze this Reddit post and extract actionable advice if present.

Post Title: {title}
Post Body: {body}
{comments_section}

If this post contains useful, actionable advice for indie game developers (marketing tips, development advice, community building, launch strategies, social media tactics, etc.), extract it as JSON:
{{
  "platform_targets": ["platforms this applies to, e.g. steam, tiktok, instagram, twitter, youtube, discord"],
  "niche": "the niche or industry (e.g. indie games, mobile games, game dev)",
  "tactic": "short summary of the actionable advice (1-2 sentences)",
  "steps": [
    {{"step": 1, "action": "first action to take"}},
    {{"step": 2, "action": "second action to take"}}
  ],
  "confidence": 0.0 to 1.0 (how confident you are this is useful advice)
}}

If this post does NOT contain actionable advice (e.g., it's just news, a question without good answers, venting, or off-topic), respond with: null

Respond ONLY with valid JSON or the word null. No explanations."""


def extract_strategy_card(
    title: str,
    body: str,
    top_comments: list[str],
    permalink: str
) -> Optional[Dict[str, Any]]:
    """
    Attempt to extract a Strategy Card from the content.
    
    Args:
        title: Post title
        body: Post body
        top_comments: List of top comment bodies
        permalink: URL to the post
        
    Returns:
        Dict matching STRATEGY_CARD_SCHEMA or None
    """
    if not LLM_ENABLED:
        return None
    
    # Build comments section
    comments_section = ""
    if top_comments:
        comments_section = "Top Comments:\n" + "\n".join(f"- {c[:300]}" for c in top_comments[:3])
    
    prompt = EXTRACTION_PROMPT.format(
        title=title[:500],
        body=body[:2000],
        comments_section=comments_section
    )
    
    if LLM_PROVIDER == "mock":
        return _mock_extraction(permalink)
    elif LLM_PROVIDER == "ollama":
        return _ollama_extraction(prompt, permalink)
    else:
        log.warning(f"LLM provider '{LLM_PROVIDER}' not supported, skipping extraction")
        return None


def _ollama_extraction(prompt: str, permalink: str) -> Optional[Dict[str, Any]]:
    """Call Ollama API to extract strategy card."""
    try:
        url = f"{OLLAMA_HOST}/api/chat"
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 500
            }
        }
        
        log.info(f"Calling Ollama for strategy extraction: {OLLAMA_HOST}")
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        content = result.get("message", {}).get("content", "").strip()
        
        log.info(f"Ollama response: {content[:300]}...")
        
        # Handle null response
        if content.lower() == "null" or not content:
            log.debug("LLM returned null - no strategy card for this post")
            return None
        
        # Try to parse JSON
        # Sometimes LLM wraps in code blocks
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        
        card = json.loads(content)
        
        # Handle list response (sometimes LLM returns multiple strategies)
        if isinstance(card, list):
            if len(card) > 0:
                card = card[0]  # Take the first one
            else:
                return None
        
        # Add evidence with permalink
        if "evidence" not in card:
            card["evidence"] = {}
        card["evidence"]["permalink"] = permalink
        
        # Validate required fields
        if not card.get("tactic") or not card.get("platform_targets"):
            log.warning("LLM returned card missing required fields")
            return None
            
        log.info(f"Extracted strategy card: {card.get('tactic', 'unknown')[:50]}")
        return card
        
    except requests.exceptions.Timeout:
        log.error("Ollama request timed out")
        return None
    except requests.exceptions.RequestException as e:
        log.error(f"Ollama request failed: {e}")
        return None
    except json.JSONDecodeError as e:
        log.warning(f"Failed to parse LLM response as JSON: {e}")
        return None
    except Exception as e:
        log.error(f"Unexpected error in strategy extraction: {e}")
        return None


def _mock_extraction(permalink: str) -> Dict[str, Any]:
    """Return a mock strategy card for testing."""
    return {
        "platform_targets": ["tiktok", "instagram"],
        "niche": "indie games",
        "tactic": "Use vertical slice gameplay loops",
        "steps": [
            {"step": 1, "action": "Record 15s of core loop"},
            {"step": 2, "action": "Add trending audio"}
        ],
        "preconditions": {"needs_gameplay_footage": True},
        "metrics": {"primary": "retention_rate", "secondary": ["shares"]},
        "risks": ["low_quality_footage"],
        "confidence": 0.85,
        "evidence": {
            "quote_snippets": ["vertical slice is key", "trending audio helps"],
            "permalink": permalink
        }
    }


def enforce_evidence_limits(card_data: Dict[str, Any]) -> Dict[str, Any]:
    """Enforce word limits on evidence snippets."""
    if "evidence" in card_data and "quote_snippets" in card_data["evidence"]:
        snippets = card_data["evidence"]["quote_snippets"]
        card_data["evidence"]["quote_snippets"] = [
            truncate_text(s, max_words=20) for s in snippets
        ]
    return card_data

