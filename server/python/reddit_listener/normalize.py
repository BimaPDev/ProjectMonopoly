"""
Text Normalization Module
=========================

Strips/normalizes markdown, masks PII (usernames, emails, phones),
and detects removed/deleted content.
"""

import re
import logging
from typing import Tuple

log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Patterns for PII detection and masking
# ─────────────────────────────────────────────────────────────────────────────

# Reddit usernames: u/username or /u/username
REDDIT_USER_PATTERN = re.compile(r"/?u/[\w-]+", re.IGNORECASE)

# Subreddit mentions: r/subreddit or /r/subreddit
REDDIT_SUB_PATTERN = re.compile(r"/?r/[\w-]+", re.IGNORECASE)

# Email addresses
EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE
)

# Phone numbers (various formats)
PHONE_PATTERN = re.compile(
    r"""
    (?:
        (?:\+?1[-.\s]?)?              # Optional country code
        (?:\(?\d{3}\)?[-.\s]?)        # Area code
        \d{3}[-.\s]?                  # First 3 digits
        \d{4}                         # Last 4 digits
    )
    """,
    re.VERBOSE
)

# ─────────────────────────────────────────────────────────────────────────────
# Markdown patterns to strip/normalize
# ─────────────────────────────────────────────────────────────────────────────

# Headers: # Header, ## Header, etc.
HEADER_PATTERN = re.compile(r"^#{1,6}\s+", re.MULTILINE)

# Bold/italic: **text**, *text*, __text__, _text_
BOLD_ITALIC_PATTERN = re.compile(r"(\*{1,2}|_{1,2})(.+?)\1")

# Strikethrough: ~~text~~
STRIKETHROUGH_PATTERN = re.compile(r"~~(.+?)~~")

# Links: [text](url) -> text (url)
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

# Inline code: `code`
INLINE_CODE_PATTERN = re.compile(r"`([^`]+)`")

# Code blocks: ```code``` or indented code
CODE_BLOCK_PATTERN = re.compile(r"```[\s\S]*?```", re.MULTILINE)
INDENTED_CODE_PATTERN = re.compile(r"^(?: {4}|\t).+$", re.MULTILINE)

# Blockquotes: > quote
BLOCKQUOTE_PATTERN = re.compile(r"^>\s*", re.MULTILINE)

# Horizontal rules: ---, ***, ___
HR_PATTERN = re.compile(r"^[-*_]{3,}$", re.MULTILINE)

# Multiple newlines -> single newline
MULTI_NEWLINE_PATTERN = re.compile(r"\n{3,}")

# Multiple spaces -> single space
MULTI_SPACE_PATTERN = re.compile(r"  +")


def normalize_markdown(text: str) -> str:
    """
    Strip/normalize markdown formatting from text.
    
    Preserves content but removes formatting syntax.
    """
    if not text:
        return ""
    
    # Remove code blocks first (preserve content indication)
    text = CODE_BLOCK_PATTERN.sub("[code block]", text)
    text = INDENTED_CODE_PATTERN.sub("", text)
    
    # Remove headers (keep the text)
    text = HEADER_PATTERN.sub("", text)
    
    # Remove bold/italic markers (keep the text)
    text = BOLD_ITALIC_PATTERN.sub(r"\2", text)
    
    # Remove strikethrough (keep the text)
    text = STRIKETHROUGH_PATTERN.sub(r"\1", text)
    
    # Convert links to: text (url)
    text = LINK_PATTERN.sub(r"\1", text)
    
    # Remove inline code markers (keep the text)
    text = INLINE_CODE_PATTERN.sub(r"\1", text)
    
    # Remove blockquote markers
    text = BLOCKQUOTE_PATTERN.sub("", text)
    
    # Remove horizontal rules
    text = HR_PATTERN.sub("", text)
    
    # Normalize whitespace
    text = MULTI_NEWLINE_PATTERN.sub("\n\n", text)
    text = MULTI_SPACE_PATTERN.sub(" ", text)
    
    return text.strip()


def mask_pii(text: str, mask_usernames: bool = True) -> str:
    """
    Mask personally identifiable information in text.
    
    Args:
        text: Input text
        mask_usernames: If True, mask Reddit usernames with [user]
        
    Returns:
        Text with PII masked
    """
    if not text:
        return ""
    
    # Mask usernames
    if mask_usernames:
        text = REDDIT_USER_PATTERN.sub("[user]", text)
    
    # Mask emails
    text = EMAIL_PATTERN.sub("[email]", text)
    
    # Mask phone numbers
    text = PHONE_PATTERN.sub("[phone]", text)
    
    return text


def detect_removed_deleted(text: str, author: str = "") -> Tuple[bool, bool]:
    """
    Detect if content has been removed or deleted.
    
    Returns:
        (is_removed, is_deleted) tuple
    """
    if not text:
        return (False, False)
    
    text_lower = text.lower().strip()
    
    is_removed = text_lower in ("[removed]", "[removed by reddit]")
    is_deleted = text_lower == "[deleted]" or author == "[deleted]"
    
    return (is_removed, is_deleted)


def normalize_text(
    text: str,
    author: str = "",
    strip_markdown: bool = True,
    mask_pii_data: bool = True,
) -> Tuple[str, bool, bool]:
    """
    Full text normalization pipeline.
    
    Args:
        text: Input text
        author: Author name (to detect deleted accounts)
        strip_markdown: Whether to strip markdown formatting
        mask_pii_data: Whether to mask PII
        
    Returns:
        (normalized_text, is_removed, is_deleted)
    """
    is_removed, is_deleted = detect_removed_deleted(text, author)
    
    if is_removed or is_deleted:
        return ("", is_removed, is_deleted)
    
    result = text
    
    if strip_markdown:
        result = normalize_markdown(result)
    
    if mask_pii_data:
        result = mask_pii(result)
    
    return (result, is_removed, is_deleted)


def truncate_text(text: str, max_words: int = 20) -> str:
    """
    Truncate text to a maximum number of words.
    
    Used for evidence snippets in Strategy Cards.
    """
    if not text:
        return ""
    
    words = text.split()
    if len(words) <= max_words:
        return text
    
    return " ".join(words[:max_words]) + "..."
