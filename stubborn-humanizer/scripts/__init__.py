"""
Stubborn Humanizer Package.
Cascading 3-stage humanization engine for resistant academic prose.
Stage 0 (Heuristic Typographic & Syntactic Variance),
Stage 1 (Automated 2-Strike Verification Gate),
Stage 2 (Micro-chunk Token Slicing <180 words & JSON HITL Candidate Resolver).
Auto-scaffolds: ./<file_stem>/<version>/humanized/
"""

from .heuristics import apply_stage0_heuristics
from .token_slicer import slice_tokens_micro
from .hitl_resolver import StubbornHumanizer

__all__ = ["apply_stage0_heuristics", "slice_tokens_micro", "StubbornHumanizer"]
