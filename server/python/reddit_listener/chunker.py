"""
Chunking Module
===============

RAG-ready chunking logic.
Splits text into chunks, prevents prompt injection, and hashes content.
"""

import hashlib
import logging
from typing import List, Tuple

from .config import CHUNK_MIN_CHARS, CHUNK_MAX_CHARS, CHUNK_OVERLAP_PERCENT

log = logging.getLogger(__name__)


def create_chunks(
    text: str,
    metadata_header: str,
) -> List[Tuple[str, str]]:
    """
    Split text into chunks with metadata header.
    
    Args:
        text: The body text to chunk
        metadata_header: Header string to prepend to each chunk
        
    Returns:
        List of (chunk_text, chunk_hash) tuples
    """
    if not text:
        return []
        
    # Guardrail: Wrap potentially unsafe content
    # We use a clear delimiter pattern that LLMs can be instructed to ignore
    safe_text = f"""
!!! START UNTRUSTED CONTENT !!!
{text}
!!! END UNTRUSTED CONTENT !!!
""".strip()
    
    full_text = f"{metadata_header}\n{safe_text}"
    
    # Simple character-based chunking with overlap
    # In a real production system, we might use tiktoken
    chunk_size = CHUNK_MAX_CHARS
    overlap_size = int(chunk_size * CHUNK_OVERLAP_PERCENT)
    
    chunks = []
    start = 0
    text_len = len(full_text)
    
    while start < text_len:
        end = min(start + chunk_size, text_len)
        
        # If we're not at the end, try to find a natural break point (newline or space)
        if end < text_len:
            # Look backwards for double newline (paragraph break)
            last_para = full_text.rfind('\n\n', start, end)
            if last_para != -1 and last_para > start + chunk_size * 0.5:
                end = last_para + 2
            else:
                # Look for single newline
                last_line = full_text.rfind('\n', start, end)
                if last_line != -1 and last_line > start + chunk_size * 0.5:
                    end = last_line + 1
                else:
                    # Look for space
                    last_space = full_text.rfind(' ', start, end)
                    if last_space != -1 and last_space > start + chunk_size * 0.5:
                        end = last_space + 1
        
        chunk_content = full_text[start:end].strip()
        if len(chunk_content) >= CHUNK_MIN_CHARS:
             # Calculate hash
            chunk_hash = hashlib.sha256(chunk_content.encode('utf-8')).hexdigest()
            chunks.append((chunk_content, chunk_hash))
        
        start += (chunk_size - overlap_size)
    
    return chunks


def build_metadata_header(
    subreddit: str,
    score: int,
    created_utc: str,
    url: str,
    title: str = "",
) -> str:
    """Build a standard metadata header for chunks."""
    header = f"[r/{subreddit} | {score} pts | {created_utc}]"
    if title:
        header += f"\nTitle: {title}"
    header += f"\nURL: {url}"
    header += "\n---"
    return header
