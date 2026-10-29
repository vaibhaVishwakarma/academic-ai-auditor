"""
Header Docstring:
Role: Command-line interface for the ai-detector-auditor skill.
Stage: Auditing & Metric Extraction.
Execution Pattern: ./.venv/bin/python -m scripts.ai_detector_auditor.cli [options]
Inputs: CLI arguments (--manifest OR --file-stem and --version, --workers, --headless, --output-dir).
Outputs: scan_session_manifest.json, audit_summary.json, and audit_report.md.
"""

from __future__ import annotations
import argparse
from pathlib import Path
from scripts.ai_detector_auditor.auditor_engine import AIDetectorAuditor

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run multi-worker parallel AI detection audits with visible-digit gating and screenshot proof."
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default=None,
        help="Path to chunk_manifest.json. If omitted, derived from --file-stem and --version.",
    )
    parser.add_argument(
        "--file-stem",
        type=str,
        default=None,
        help="Document stem name (e.g. 'thesis'). Used to locate ./<file_stem>/<version>/chunks/chunk_manifest.json.",
    )
    parser.add_argument(
        "--version",
        type=str,
        default="v1",
        help="Iteration version identifier. Default: v1",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=2,
        help="Number of concurrent Chrome browser contexts (1-8). Default: 2",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Run Chrome in headless mode. Default: False (visible GUI tiling)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Custom output directory override. Defaults to ./<file_stem>/<version>/ai-score/",
    )

    args = parser.parse_args()

    # Determine manifest path
    manifest_path: Path
    if args.manifest:
        manifest_path = Path(args.manifest)
    elif args.file_stem:
        manifest_path = Path.cwd() / args.file_stem / args.version / "chunks" / "chunk_manifest.json"
    else:
        parser.error("Either --manifest or --file-stem must be specified.")

    auditor = AIDetectorAuditor(
        manifest_path=manifest_path,
        workers=args.workers,
        headless=args.headless,
        output_dir=args.output_dir,
    )

    auditor.run_audit()

if __name__ == "__main__":
    main()
