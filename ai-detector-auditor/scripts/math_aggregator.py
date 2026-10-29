"""
Header Docstring:
Role: Dual mathematical reporting engine for manuscript AI audits.
Stage: Post-Audit Aggregation & Statistical Certification.
Inputs: List of evaluated chunk results with scores and word counts.
Outputs: Typed statistical summary dictionary and formatted Markdown table.
Formulas:
  - Simple Average: (1 / M) * sum(S_i)
  - Weighted Average: sum(S_i * W_i) / sum(W_i)
"""

from __future__ import annotations
from typing import Dict, List, Any
import datetime

def compute_audit_statistics(
    results: List[Dict[str, Any]],
    document_name: str,
    file_stem: str,
    version: str,
) -> Dict[str, Any]:
    """
    Computes both simple arithmetic average and word-weighted average across all chunks,
    along with zero-score counts and max score anomalies.
    """
    if not results:
        raise ValueError("Cannot compute statistics on empty results list.")

    valid_results = [r for r in results if r.get("score_percent") is not None]
    if not valid_results:
        raise ValueError("No valid scores found in audit results.")

    total_chunks = len(valid_results)
    total_words = sum(r.get("word_count", 0) for r in valid_results)

    simple_sum = sum(r["score_percent"] for r in valid_results)
    simple_avg = round(simple_sum / total_chunks, 2)

    if total_words > 0:
        weighted_sum = sum(r["score_percent"] * r.get("word_count", 0) for r in valid_results)
        weighted_avg = round(weighted_sum / total_words, 2)
    else:
        weighted_avg = simple_avg

    zero_count = sum(1 for r in valid_results if r["score_percent"] == 0)
    zero_pct = round((zero_count / total_chunks) * 100, 2)

    # Identify highest scoring chunk
    worst_chunk = max(valid_results, key=lambda r: r["score_percent"])

    summary: Dict[str, Any] = {
        "audit_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "document_name": document_name,
        "file_stem": file_stem,
        "version": version,
        "total_chunks_scanned": total_chunks,
        "total_words_evaluated": total_words,
        "simple_average_score": simple_avg,
        "weighted_average_score": weighted_avg,
        "zero_detection_count": zero_count,
        "zero_detection_percentage": zero_pct,
        "max_score_chunk": {
            "chunk_id": worst_chunk.get("chunk_id"),
            "page_start": worst_chunk.get("start_page"),
            "score": worst_chunk["score_percent"],
            "screenshot_path": worst_chunk.get("screenshot_path"),
        },
        "chunk_breakdown": [
            {
                "chunk_id": r.get("chunk_id"),
                "pages": f"p{r.get('start_page', 0):02d}-p{r.get('end_page', 0):02d}" if r.get('start_page') != r.get('end_page') else f"p{r.get('start_page', 0):02d}",
                "word_count": r.get("word_count", 0),
                "score_percent": r.get("score_percent"),
                "screenshot": r.get("screenshot_path"),
                "scan_attempts": r.get("attempts_needed", 1),
            }
            for r in valid_results
        ],
    }

    return summary

def generate_markdown_report(summary: Dict[str, Any]) -> str:
    """Generates an authoritative GitHub-flavored Markdown report."""
    md = []
    md.append(f"# AI Detection Audit Report: `{summary['document_name']}` ({summary['version']})")
    md.append(f"\n*Audit Completed: {summary['audit_timestamp']}*")
    md.append("\n## Executive Summary")
    md.append(f"- **Total Chunks Scanned**: {summary['total_chunks_scanned']}")
    md.append(f"- **Total Words Evaluated**: {summary['total_words_evaluated']}")
    md.append(f"- **Simple Arithmetic Average**: `{summary['simple_average_score']}%`")
    md.append(f"- **Word-Weighted Average**: `{summary['weighted_average_score']}%`")
    md.append(f"- **Zero-AI Chunks**: {summary['zero_detection_count']} / {summary['total_chunks_scanned']} ({summary['zero_detection_percentage']}%)")
    md.append(f"- **Peak Score**: `{summary['max_score_chunk']['score']}%` (Chunk `{summary['max_score_chunk']['chunk_id']}`)")
    
    md.append("\n## Chunk Scorecard")
    md.append("| Chunk ID | Pages | Word Count | AI Score | Attempts | Screenshot Proof |")
    md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
    
    for row in summary["chunk_breakdown"]:
        shot_link = f"[Screenshot]({row['screenshot']})" if row.get("screenshot") else "N/A"
        md.append(f"| `{row['chunk_id']}` | {row['pages']} | {row['word_count']} | **{row['score_percent']}%** | {row['scan_attempts']} | {shot_link} |")

    return "\n".join(md)
