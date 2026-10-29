"""
AI Detector Auditor Package.
Parallel multi-worker browser orchestration for automated, verifiable AI audits.
Enforces anti-false-zero visible digit assertions (regex ^\\d{1,3}%$)
and auto-scaffolds: ./<file_stem>/<version>/ai-score/screenshots/
"""

from .auditor_engine import AIDetectorAuditor
from .math_aggregator import compute_audit_statistics

__all__ = ["AIDetectorAuditor", "compute_audit_statistics"]
