"""
Header Docstring:
Role: Stage 0 deterministic typography and syntactic variance transforms.
Stage: Humanization Pipeline (Stage 0).
Inputs: Raw text string, optional random seed for reproducibility.
Outputs: Mutated candidate string with authentic human cadence and stripped AI markers.
Rules:
- Strip all em-dashes (—), en-dashes (–), and double-dashes (--).
- Normalize non-standard arrows (<-- to <-).
- Inject sparse human-like parenthesis spacing.
- Sparsely vary conjunctions (& vs and).
- Invert passive/active framing without altering facts.
"""

from __future__ import annotations
import random
import re
from typing import Optional

def clean_punctuation_and_arrows(text: str) -> str:
    """
    Normalizes typography:
    - Replaces '<--' with '<-' and '==>' with '->'
    - Strips em-dashes ('—'), en-dashes ('–'), and double-dashes ('--')
    """
    text = text.replace("<--", "<-").replace("==>", "->")
    # Replace em-dashes and double-dashes with commas or hyphens
    text = re.sub(r"\s*[—–]\s*|\s*--\s*", ", ", text)
    # Double check passes
    text = text.replace("<--", "<-")
    # Clean up duplicate punctuation and spacing around commas
    text = re.sub(r"\s*,\s*,+", ",", text)
    text = re.sub(r"\s+,", ",", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def inject_sparse_parentheses(text: str, rate: float = 0.35, seed: Optional[int] = None) -> str:
    """
    Disrupts uniform token cadence by introducing natural human typographical spacing inside parentheses:
    - Standard: (xyz)
    - Both sides: ( xyz )
    - Left only: ( xyz)
    - Right only: (xyz )
    """
    rng = random.Random(seed) if seed is not None else random

    def repl(match: re.Match) -> str:
        inner = match.group(1).strip()
        if not inner or "(" in inner or ")" in inner:
            return match.group(0)

        if rng.random() > rate:
            return f"({inner})"

        choice = rng.choice(["both", "left", "right"])
        if choice == "both":
            return f"( {inner} )"
        elif choice == "left":
            return f"( {inner})"
        else:
            return f"({inner} )"

    return re.sub(r"\(([^()]+)\)", repl, text)

def inject_conjunction_variance(text: str, rate: float = 0.20, seed: Optional[int] = None) -> str:
    """
    Sparsely alternates 'and' with '&' in compound phrases to inject human variety,
    avoiding citations or mathematical formulas.
    """
    rng = random.Random(seed) if seed is not None else random
    tokens = re.split(r"(\s+and\s+)", text)
    result = []
    for token in tokens:
        if token.strip() == "and" and rng.random() < rate:
            result.append(" & ")
        else:
            result.append(token)
    return "".join(result)

def inject_voice_and_cadence_variance(text: str, seed: Optional[int] = None) -> str:
    """
    Applies subject-object inversions (active <-> passive) and subtle cadence adjustments
    to disrupt predictable LLM syntactic structures without changing semantic meaning.
    """
    rng = random.Random(seed) if seed is not None else random

    transformations = [
        (r"\bwe evaluated\b", "our evaluation examined"),
        (r"\bwe observed\b", "observations indicated that"),
        (r"\bwe formulate\b", "our formulation presents"),
        (r"\bwe propose\b", "this paper introduces"),
        (r"\bwe demonstrate\b", "the empirical results establish"),
        (r"\bFurthermore,\b", "In addition,"),
        (r"\bMoreover,\b", "Beyond this,"),
        (r"\bIn conclusion,\b", "Overall,"),
        (r"\bConsequently,\b", "As a result,"),
    ]

    for pat, rep in transformations:
        if re.search(pat, text, re.IGNORECASE) and rng.random() < 0.65:
            text = re.sub(pat, rep, text, count=1, flags=re.IGNORECASE)

    return text

def apply_stage0_heuristics(text: str, seed: Optional[int] = None) -> str:
    """Applies all Stage 0 heuristic transforms in pipeline sequence."""
    text = clean_punctuation_and_arrows(text)
    text = inject_sparse_parentheses(text, seed=seed)
    text = inject_conjunction_variance(text, seed=seed)
    text = inject_voice_and_cadence_variance(text, seed=seed)
    return text.strip()
