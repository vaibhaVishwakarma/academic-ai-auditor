"""
Manuscript PDF Slicer Package.
Enforces Ghostscript /ebook stream compression (<2.10MB platform upload ceiling)
and auto-scaffolds: ./<file_stem>/<version>/chunks/
"""

from .slicer_engine import ManuscriptSlicer

__all__ = ["ManuscriptSlicer"]
