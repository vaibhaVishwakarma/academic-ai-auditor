"""
Header Docstring:
Role: Micro-chunk token slicer for external auxiliary humanization platforms.
Stage: Humanization Pipeline (Stage 2 Partitioning).
Inputs: Long paragraph or section text.
Outputs: List of micro-chunks strictly < 180 words, split along sentence boundaries.
Invariant: Never submit > 180 words to auxiliary web tools (prevents HTTP 400 rejection ceiling).
"""

from __future__ import annotations
import re
from typing import List

def slice_tokens_micro(text: str, max_words: int = 175) -> List[str]:
    """
    Partitions long text into continuous micro-chunks strictly < max_words (default 175),
    respecting sentence boundaries (period, question mark, newline).
    """
    text = text.strip()
    if not text:
        return []

    words = text.split()
    if len(words) <= max_words:
        return [text]

    # Split into sentences preserving punctuation
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: List[str] = []
    current_sentences: List[str] = []
    current_word_count = 0

    for sent in sentences:
        sent_words = len(sent.split())

        # If a single sentence exceeds max_words, split along commas/semicolons
        if sent_words > max_words:
            sub_clauses = re.split(r"(?<=[,;])\s+", sent)
            for clause in sub_clauses:
                clause_words = len(clause.split())
                if current_word_count + clause_words > max_words and current_sentences:
                    chunks.append(" ".join(current_sentences))
                    current_sentences = [clause]
                    current_word_count = clause_words
                else:
                    current_sentences.append(clause)
                    current_word_count += clause_words
            continue

        if current_word_count + sent_words > max_words and current_sentences:
            chunks.append(" ".join(current_sentences))
            current_sentences = [sent]
            current_word_count = sent_words
        else:
            current_sentences.append(sent)
            current_word_count += sent_words

    if current_sentences:
        chunks.append(" ".join(current_sentences))

    return chunks

def stitch_micro_chunks(chunks: List[str]) -> str:
    """Reassembles micro-chunks into a continuous paragraph."""
    return " ".join(c.strip() for c in chunks if c.strip())
