"""
Header Docstring:
Role: Cascading 3-stage humanization manager and HITL candidate resolver.
Stage: Remediation & Re-Audit Preparation (Stage 3 of Manuscript Audit Pipeline).
Inputs: scan_session_manifest.json from ./<file_stem>/<version>/ai-score/, target score threshold.
Outputs: humanizer_manifest.json in ./<file_stem>/<version>/humanized/ and v2 workspace branch.
Invariants:
- Never declare a paragraph resolved without recording candidate mutations and verified scores.
- Scope all candidates and manifests inside ./<file_stem>/<version>/humanized/.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import re

from scripts.stubborn_humanizer.heuristics import apply_stage0_heuristics
from scripts.stubborn_humanizer.token_slicer import slice_tokens_micro

class StubbornHumanizer:
    """
    Manages cascading humanization stages (Stage 0 heuristics -> Stage 1 2-strike -> Stage 2 HITL)
    and branches remediated documents into v2 workspaces.
    """

    def __init__(
        self,
        file_stem: str,
        version: str = "v1",
        threshold: int = 15,
        output_dir: Optional[Path | str] = None,
    ) -> None:
        self.file_stem = file_stem
        self.version = version
        self.threshold = threshold

        # Scoped workspace roots
        self.workspace_root = Path.cwd() / self.file_stem / self.version
        self.ai_score_dir = self.workspace_root / "ai-score"
        
        if output_dir:
            self.output_dir = Path(output_dir).resolve()
        else:
            self.output_dir = self.workspace_root / "humanized"

        self.candidates_dir = self.output_dir / "candidates"
        self.candidates_dir.mkdir(parents=True, exist_ok=True)

    def load_audit_manifest(self) -> Dict[str, Any]:
        """Loads scan session telemetry from current version."""
        manifest_path = self.ai_score_dir / "scan_session_manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(
                f"Scan session manifest not found at: {manifest_path}. Run ai-detector-auditor first."
            )
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def generate_candidates(self, raw_text: str, num_variants: int = 3) -> List[Dict[str, Any]]:
        """Generates multi-variant candidates using diverse Stage 0 heuristic seeds."""
        candidates = []
        for i in range(1, num_variants + 1):
            seed_val = 42 + i * 17
            mutated = apply_stage0_heuristics(raw_text, seed=seed_val)
            candidates.append({
                "candidate_id": f"cand_{i:02d}",
                "stage": 0,
                "text": mutated,
                "word_count": len(mutated.split()),
                "status": "PENDING_VERIFICATION",
                "strike_number": 1,
            })
        return candidates

    def process_high_scoring_chunks(self) -> Dict[str, Any]:
        """
        Scans audit results, extracts chunks scoring above threshold, and generates
        humanizer_manifest.json with candidate mutations.
        """
        audit_data = self.load_audit_manifest()
        results = audit_data.get("results", [])

        flagged_chunks = [
            r for r in results
            if r.get("score_percent") is not None and r["score_percent"] > self.threshold
        ]

        print(f"[*] Found {len(flagged_chunks)} chunks exceeding threshold ({self.threshold}%)...")

        remediation_entries = []
        for chunk in flagged_chunks:
            chunk_id = chunk["chunk_id"]
            orig_score = chunk["score_percent"]
            chunk_file = Path(chunk.get("screenshot_path", "")).parent.parent / "chunks" / f"page_{chunk['start_page']:02d}.pdf"

            # Generate candidate mutations
            # In production, extracted text is read from chunk or manifest
            dummy_text = f"Evaluated page {chunk['start_page']} exhibits AI patterns with score {orig_score}%."
            candidates = self.generate_candidates(dummy_text)

            remediation_entries.append({
                "chunk_id": chunk_id,
                "page_number": chunk["start_page"],
                "baseline_ai_score": orig_score,
                "target_threshold": self.threshold,
                "candidates": candidates,
                "status": "IN_REMEDIATION",
            })

        humanizer_manifest = {
            "manifest_version": "1.0.0",
            "file_stem": self.file_stem,
            "version": self.version,
            "threshold": self.threshold,
            "total_chunks_remediated": len(remediation_entries),
            "remediations": remediation_entries,
        }

        manifest_path = self.output_dir / "humanizer_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(humanizer_manifest, f, indent=2)

        print(f"[✓] Candidate manifest generated: {manifest_path}")

        # Auto-scaffold next version branch (v2)
        next_version = "v2" if self.version == "v1" else f"v{int(self.version.replace('v', '')) + 1}"
        next_workspace = Path.cwd() / self.file_stem / next_version
        next_workspace.mkdir(parents=True, exist_ok=True)
        print(f"[✓] Pre-scaffolded next version workspace: {next_workspace}")

        return humanizer_manifest
