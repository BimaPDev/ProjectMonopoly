"""
AI Content Generator
=====================

Generates social media captions, hooks, and hashtags using LLM.
Integrates all context from the aggregator for grounded content.

Supports:
    - Ollama (local)
    - Gemini (cloud)

Author: ProjectMonopoly Team
"""

import os
import json
import logging
import requests
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from .context_aggregator import ContentContext

log = logging.getLogger(__name__)

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b-instruct")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


@dataclass
class GeneratedContent:
    """AI-generated content for social media post."""
    title: str = ""
    caption: str = ""
    hook: str = ""
    hashtags: List[str] = None
    confidence: str = "low"
    error: str = ""
    
    def __post_init__(self):
        if self.hashtags is None:
            self.hashtags = []


def generate_content(
    context: ContentContext,
    platform: str = "instagram",
    custom_instructions: str = ""
) -> GeneratedContent:
    """
    Generate caption, hook, and hashtags using LLM.
    
    Args:
        context: Aggregated ContentContext with all data
        platform: Target platform (instagram, tiktok)
        custom_instructions: Optional user-provided instructions
        
    Returns:
        GeneratedContent with title, caption, hook, hashtags
    """
    result = GeneratedContent()
    
    if not context.game_title:
        result.error = "No game context available"
        return result
    
    try:
        # Build the prompt
        prompt = _build_prompt(context, platform, custom_instructions)
        
        # Call LLM
        if LLM_PROVIDER == "gemini" and GEMINI_API_KEY:
            response = _call_gemini(prompt)
        else:
            response = _call_ollama(prompt)
        
        # Parse response
        result = _parse_response(response, context.top_hashtags)
        result.confidence = context.confidence
        
        log.info(
            "Generated content: hook=%s... hashtags=%d",
            result.hook[:50] if result.hook else "N/A",
            len(result.hashtags)
        )
        
    except Exception as e:
        log.exception("Content generation failed: %s", e)
        result.error = str(e)
    
    return result


def _build_prompt(
    ctx: ContentContext, 
    platform: str, 
    custom_instructions: str
) -> str:
    """Build the LLM prompt with all context."""
    
    prompt = f"""You are a social media content creator for indie games. Generate engaging {platform} content.

GAME CONTEXT:
- Title: {ctx.game_title}
- Genre: {ctx.genre or 'Not specified'}
- Tone: {ctx.tone or 'Fun and engaging'}
- Audience: {ctx.audience or 'Gamers'}
- Key Mechanics: {ctx.key_mechanics or 'Not specified'}

"""
    
    # Add document context
    if ctx.doc_chunks:
        prompt += "GAME FEATURES (from documentation):\n"
        for i, chunk in enumerate(ctx.doc_chunks, 1):
            # Truncate long chunks
            snippet = chunk[:300] + "..." if len(chunk) > 300 else chunk
            prompt += f"{i}. {snippet}\n"
        prompt += "\n"
    
    # Add competitor context
    if ctx.top_hooks:
        prompt += "COMPETITOR HOOKS (use as inspiration, don't copy):\n"
        for i, hook in enumerate(ctx.top_hooks, 1):
            prompt += f"{i}. {hook}\n"
        prompt += "\n"
    
    # Add viral hooks (high-impact outliers from outlier detection system)
    if ctx.viral_hooks:
        prompt += "🔥 VIRAL HOOKS (proven 10x-100x performers - study these patterns closely):\n"
        for i, vh in enumerate(ctx.viral_hooks, 1):
            multiplier = vh.get('multiplier', 10)
            engagement = vh.get('engagement', 0)
            hook_text = vh.get('hook', '')[:200]  # Truncate for token efficiency
            badge = "🔥" if multiplier >= 100 else "⚡" if multiplier >= 50 else "📈"
            prompt += f"{i}. {badge} [{multiplier}x] {hook_text}\n"
        prompt += "\nThese hooks outperformed typical content by 10-100x. Adapt their patterns!\n\n"
    
    if ctx.top_hashtags:
        prompt += f"ALLOWED HASHTAGS (ONLY use these): {', '.join('#' + h for h in ctx.top_hashtags)}\n\n"
    
    if ctx.competitor_handles:
        prompt += f"DIFFERENTIATE FROM: @{', @'.join(ctx.competitor_handles)}\n\n"
    
    # Add Reddit tactics
    if ctx.strategy_cards:
        prompt += "PROVEN TACTICS (from community):\n"
        for i, card in enumerate(ctx.strategy_cards, 1):
            prompt += f"{i}. {card['tactic']}"
            if card.get('steps'):
                prompt += f" - {card['steps'][:100]}"
            prompt += "\n"
        prompt += "\n"
    
    if ctx.trending_topics:
        prompt += f"TRENDING TOPICS: {', '.join(ctx.trending_topics[:3])}\n\n"
    
    # Platform-specific guidelines
    if platform == "instagram":
        prompt += """INSTAGRAM GUIDELINES:
- Caption: 150-300 characters
- Hook: First line must grab attention
- Use 3-5 hashtags from the allowed list
- Include a soft call-to-action
"""
    elif platform == "tiktok":
        prompt += """TIKTOK GUIDELINES:
- Caption: Short and punchy (100-150 characters)
- Hook: Must be attention-grabbing for first 3 seconds
- Use 2-4 hashtags from the allowed list
- Trendy, conversational tone
"""
    
    if custom_instructions:
        prompt += f"\nADDITIONAL INSTRUCTIONS:\n{custom_instructions}\n"
    
    prompt += """
TASK: Generate content for this game's social media post.

Respond in this exact JSON format:
{
    "hook": "First line to grab attention (max 50 chars)",
    "caption": "Full caption with hook included",
    "hashtags": ["hashtag1", "hashtag2", "hashtag3"]
}

Only use hashtags from the ALLOWED HASHTAGS list. Do not invent new hashtags.
"""
    
    return prompt


def _call_ollama(prompt: str) -> str:
    """Call Ollama API for local inference."""
    url = f"{OLLAMA_HOST}/api/generate"
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
        }
    }
    
    log.debug("Calling Ollama: model=%s", OLLAMA_MODEL)
    
    response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()
    
    data = response.json()
    return data.get("response", "")


def _call_gemini(prompt: str) -> str:
    """Call Gemini API for cloud inference."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.9,
            "maxOutputTokens": 500,
        }
    }
    
    log.debug("Calling Gemini: model=%s", GEMINI_MODEL)
    
    response = requests.post(url, json=payload, timeout=60)
    response.raise_for_status()
    
    data = response.json()
    candidates = data.get("candidates", [])
    if candidates:
        parts = candidates[0].get("content", {}).get("parts", [])
        if parts:
            return parts[0].get("text", "")
    
    return ""


def _parse_response(response: str, allowed_hashtags: List[str]) -> GeneratedContent:
    """Parse LLM response and validate hashtags."""
    result = GeneratedContent()
    
    try:
        # Try to extract JSON from response
        json_start = response.find("{")
        json_end = response.rfind("}") + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = response[json_start:json_end]
            data = json.loads(json_str)
            
            result.hook = data.get("hook", "")
            result.caption = data.get("caption", "")
            result.title = result.hook  # Use hook as title
            
            # Validate hashtags against allowed list
            raw_hashtags = data.get("hashtags", [])
            allowed_set = {h.lower().strip("#") for h in allowed_hashtags}
            
            result.hashtags = []
            for tag in raw_hashtags:
                clean_tag = tag.lower().strip("#")
                if clean_tag in allowed_set:
                    result.hashtags.append(clean_tag)
            
            # If no valid hashtags, use top allowed ones
            if not result.hashtags and allowed_hashtags:
                result.hashtags = allowed_hashtags[:3]
        else:
            # Fallback: treat entire response as caption
            result.caption = response.strip()
            result.hook = response.split("\n")[0][:100] if response else ""
            result.title = result.hook
            result.hashtags = allowed_hashtags[:3] if allowed_hashtags else []
            
    except json.JSONDecodeError as e:
        log.warning("Failed to parse JSON response: %s", e)
        result.caption = response.strip()
        result.hook = response.split("\n")[0][:100] if response else ""
        result.title = result.hook
        result.hashtags = allowed_hashtags[:3] if allowed_hashtags else []
    
    return result
