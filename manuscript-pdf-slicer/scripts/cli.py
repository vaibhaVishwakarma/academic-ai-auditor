"""
Header Docstring:
Role: Command-line interface for the manuscript-pdf-slicer skill.
Stage: Preprocessing / Slicing.
Execution Pattern: ./.venv/bin/python -m scripts.manuscript_slicer.cli --source <path> [options]
Inputs: CLI arguments (--source, --version, --pages, --output-dir).
Outputs: Sliced compressed chunks and chunk_manifest.json.
"""

from __future__ import annotations
import argparse
from pathlib import Path
from typing import List, Optional
from scripts.manuscript_slicer.slicer_engine import ManuscriptSlicer

def parse_page_range(range_str: Optional[str]) -> Optional[List[int]]:
    """Parses page ranges like '1-5,8,11-14' into a sorted list of unique integers."""
    if not range_str:
        return None
    pages: set[int] = set()
    for part in range_str.split(","):
        part = part.strip()
        if "-" in part:
            start_str, end_str = part.split("-", 1)
            pages.update(range(int(start_str), int(end_str) + 1))
        else:
            pages.add(int(part))
    return sorted(list(pages))

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Slice an academic manuscript into Ghostscript-compressed, upload-safe PDF chunks."
    )
    parser.add_argument(
        "--source",
        type=str,
        required=True,
        help="Path to the input PDF manuscript.",
    )
    parser.add_argument(
        "--version",
        type=str,
        default="v1",
        help="Iteration version identifier (e.g. v1, v2). Default: v1",
    )
    parser.add_argument(
        "--pages",
        type=str,
        default=None,
        help="Optional page range (e.g. '1-5,8,11-14'). If omitted, slices all pages.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Custom output directory override. Defaults to ./<file_stem>/<version>/chunks/",
    )

    args = parser.parse_args()
    page_selection = parse_page_range(args.pages)

    slicer = ManuscriptSlicer(
        source_path=args.source,
        version=args.version,
        output_dir=args.output_dir,
    )

    print(f"[*] Slicing document: {slicer.source_path.name}")
    print(f"[*] Output directory: {slicer.output_dir}")
    manifest = slicer.slice_pages(page_selection)

    print(f"[✓] Successfully sliced {len(manifest['chunks'])} chunks ({manifest['total_words']} total words)")
    print(f"[✓] Manifest written to: {slicer.output_dir / 'chunk_manifest.json'}")

if __name__ == "__main__":
    main()
