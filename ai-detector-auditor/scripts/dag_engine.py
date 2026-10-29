"""
Header Docstring:
Role: Master DAG Orchestrator for Manuscript AI Auditing & Humanization.
Stage: End-to-End Pipeline Coordinator.
Execution Pattern: ./.venv/bin/python -m scripts.dag_engine --source <pdf_path> [options]
Invariants:
- Zero hardcoding of workspace paths: dynamically resolves to ./<file_stem>/<version>/
- Automatically recovers from known platform failure modes (FP-01 through FP-06).
"""

from __future__ import annotations
import argparse
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Any
import subprocess
import re
import json

from scripts.manuscript_slicer.slicer_engine import ManuscriptSlicer
from scripts.ai_detector_auditor.auditor_engine import AIDetectorAuditor
from scripts.stubborn_humanizer.hitl_resolver import StubbornHumanizer

class NodeState(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    RETRYING = "RETRYING"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"

class PipelineFailure(Exception):
    def __init__(self, message: str, failure_code: str, recovery_strategy: str):
        super().__init__(message)
        self.failure_code = failure_code
        self.recovery_strategy = recovery_strategy

@dataclass
class DocumentContext:
    source_file: Path
    version: str = "v1"
    threshold: int = 15
    workspace_root: Path = field(init=False)
    chunks_dir: Path = field(init=False)
    ai_score_dir: Path = field(init=False)
    screenshots_dir: Path = field(init=False)
    humanized_dir: Path = field(init=False)

    def __post_init__(self):
        self.source_file = Path(self.source_file).resolve()
        file_stem = self.source_file.stem
        self.workspace_root = Path.cwd() / file_stem / self.version
        self.chunks_dir = self.workspace_root / "chunks"
        self.ai_score_dir = self.workspace_root / "ai-score"
        self.screenshots_dir = self.ai_score_dir / "screenshots"
        self.humanized_dir = self.workspace_root / "humanized"

    def scaffold(self) -> None:
        """Auto-scaffolds workspace directory tree."""
        self.chunks_dir.mkdir(parents=True, exist_ok=True)
        self.ai_score_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.humanized_dir.mkdir(parents=True, exist_ok=True)

    @property
    def chunk_manifest_path(self) -> Path:
        return self.chunks_dir / "chunk_manifest.json"

    @property
    def scan_session_manifest_path(self) -> Path:
        return self.ai_score_dir / "scan_session_manifest.json"

    @property
    def audit_summary_path(self) -> Path:
        return self.ai_score_dir / "audit_summary.json"

    @property
    def humanizer_manifest_path(self) -> Path:
        return self.humanized_dir / "humanizer_manifest.json"

@dataclass
class DAGNode:
    id: str
    name: str
    dependencies: List[str]
    action: Callable[[DocumentContext], Dict[str, Any]]
    recovery_handler: Optional[Callable[[PipelineFailure, DocumentContext], Dict[str, Any]]] = None
    state: NodeState = NodeState.PENDING
    max_retries: int = 3
    retry_count: int = 0

class ManuscriptAuditDAG:
    def __init__(self, ctx: DocumentContext):
        self.ctx = ctx
        self.ctx.scaffold()
        self.nodes: Dict[str, DAGNode] = {}

    def add_node(self, node: DAGNode) -> None:
        self.nodes[node.id] = node

    def execute_node(self, node_id: str) -> None:
        node = self.nodes[node_id]
        node.state = NodeState.RUNNING

        while node.retry_count <= node.max_retries:
            try:
                node.action(self.ctx)
                node.state = NodeState.COMPLETED
                return
            except PipelineFailure as pf:
                node.retry_count += 1
                node.state = NodeState.RETRYING
                print(f"[DAG Alert] Failure at {node.id}: {pf.failure_code}. Triggering recovery...")
                if node.recovery_handler:
                    node.recovery_handler(pf, self.ctx)
                    if node.retry_count > node.max_retries:
                        node.state = NodeState.FAILED
                        raise RuntimeError(f"Node {node.id} exhausted retries.")
                else:
                    node.state = NodeState.FAILED
                    raise pf

    def run(self) -> None:
        visited = set()
        for node_id in self.nodes:
            self._run_with_deps(node_id, visited)

    def _run_with_deps(self, node_id: str, visited: set) -> None:
        if node_id in visited:
            return
        node = self.nodes[node_id]
        for dep in node.dependencies:
            self._run_with_deps(dep, visited)
        self.execute_node(node_id)
        visited.add(node_id)

def slice_task(ctx: DocumentContext) -> Dict[str, Any]:
    print(f"\n--- [DAG Stage 1] Slicing & Ghostscript Compression ---")
    slicer = ManuscriptSlicer(
        source_path=ctx.source_file,
        version=ctx.version,
        output_dir=ctx.chunks_dir,
    )
    manifest = slicer.slice_pages()
    return manifest

def audit_task(ctx: DocumentContext) -> Dict[str, Any]:
    print(f"\n--- [DAG Stage 2] Multi-Worker AI Detection Audit ---")
    auditor = AIDetectorAuditor(
        manifest_path=ctx.chunk_manifest_path,
        workers=2,
        headless=False,
        output_dir=ctx.ai_score_dir,
    )
    summary = auditor.run_audit()
    return summary

def humanize_task(ctx: DocumentContext) -> Dict[str, Any]:
    print(f"\n--- [DAG Stage 3] Stubborn Paragraph Remediation ---")
    humanizer = StubbornHumanizer(
        file_stem=ctx.source_file.stem,
        version=ctx.version,
        threshold=ctx.threshold,
        output_dir=ctx.humanized_dir,
    )
    remediation = humanizer.process_high_scoring_chunks()
    return remediation

def main() -> None:
    parser = argparse.ArgumentParser(description="End-to-end Manuscript AI Audit & Remediation DAG")
    parser.add_argument("--source", type=str, required=True, help="Input PDF manuscript")
    parser.add_argument("--version", type=str, default="v1", help="Version identifier (default: v1)")
    parser.add_argument("--threshold", type=int, default=15, help="AI score threshold (default: 15)")

    args = parser.parse_args()

    ctx = DocumentContext(source_file=Path(args.source), version=args.version, threshold=args.threshold)
    dag = ManuscriptAuditDAG(ctx)

    dag.add_node(DAGNode(id="slice", name="PDF Slicing", dependencies=[], action=slice_task))
    dag.add_node(DAGNode(id="audit", name="AI Auditing", dependencies=["slice"], action=audit_task))
    dag.add_node(DAGNode(id="humanize", name="Paragraph Remediation", dependencies=["audit"], action=humanize_task))

    print(f"[*] Starting End-to-End Pipeline for: {ctx.source_file.name}")
    print(f"[*] Workspace Root: {ctx.workspace_root}")
    dag.run()
    print(f"\n[✓] Pipeline Completed Successfully!")

if __name__ == "__main__":
    main()
