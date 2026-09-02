"""
TextLens — Text cleaning and sentence splitting.
Preserves page-level source information.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from loguru import logger


@dataclass
class ProcessedSentence:
    sentence_index: int       # global doc index (0-based)
    page_number: int
    text: str
    section: Optional[str] = None


def clean_text(text: str) -> str:
    """Normalize whitespace and remove control characters."""
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)  # control chars
    text = re.sub(r"\r\n|\r", "\n", text)           # normalize line endings
    text = re.sub(r"\n{3,}", "\n\n", text)          # collapse excessive blank lines
    text = re.sub(r"[ \t]{2,}", " ", text)          # collapse spaces
    text = text.strip()
    return text


def split_into_sentences(text: str) -> List[str]:
    """Rule-based sentence splitter that handles abbreviations gracefully."""
    # We use a simple heuristic: split on ". ", "! ", "? " followed by uppercase
    # but protect common abbreviations
    abbrevs = {"Mr", "Mrs", "Ms", "Dr", "Prof", "Sr", "Jr", "vs", "etc",
               "e.g", "i.e", "Fig", "No", "Vol", "pp", "Ch"}
    abbrev_pattern = "|".join(re.escape(a) for a in abbrevs)

    # Temporarily replace abbreviation periods
    text = re.sub(rf"\b({abbrev_pattern})\.", r"\1<DOT>", text)

    # Split on sentence boundaries
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z\"\(])", text)

    # Restore abbreviation dots
    sentences = [s.replace("<DOT>", ".").strip() for s in sentences]

    # Filter short/empty strings
    return [s for s in sentences if len(s.split()) >= 3]


def process_pages(pages) -> List[ProcessedSentence]:
    """
    Process a list of ExtractedPage objects into ProcessedSentence list.
    Each sentence retains its source page number.
    """
    result: List[ProcessedSentence] = []
    global_idx = 0

    for page in pages:
        cleaned = clean_text(page.text)
        sentences = split_into_sentences(cleaned)
        for sent in sentences:
            result.append(
                ProcessedSentence(
                    sentence_index=global_idx,
                    page_number=page.page_number,
                    text=sent,
                )
            )
            global_idx += 1

    logger.info(f"Processed {len(result)} sentences across {len(pages)} pages")
    return result
