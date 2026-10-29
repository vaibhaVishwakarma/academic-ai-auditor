"""
Header Docstring:
Role: Command-line interface for the stubborn-humanizer skill.
Stage: Humanization & Remediation.
Execution Pattern: ./.venv/bin/python -m scripts.stubborn_humanizer.cli [options]
Inputs: CLI arguments (--file-stem, --version, --threshold, --output-dir).
Outputs: humanizer_manifest.json and next version workspace scaffold.
"""

from __future__ import annotations
import argparse
from scripts.stubborn_humanizer.hitl_resolver import StubbornHumanizer

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run cascading 3-stage humanization on high-scoring manuscript chunks."
    )
    parser.add_argument(
        "--file-stem",
        type=str,
        required=True,
        help="Document stem name (e.g. 'thesis'). Scopes work to ./<file_stem>/<version>/",
    )
    parser.add_argument(
        "--version",
        type=str,
        default="v1",
        help="Baseline version to remediate. Default: v1",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=15,
        help="Maximum acceptable AI score percentage. Chunks above this threshold are flagged. Default: 15",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Custom output directory override. Defaults to ./<file_stem>/<version>/humanized/",
    )

    args = parser.parse_args()

    humanizer = StubbornHumanizer(
        file_stem=args.file_stem,
        version=args.version,
        threshold=args.threshold,
        output_dir=args.output_dir,
    )

    humanizer.process_high_scoring_chunks()

if __name__ == "__main__":
    main()
