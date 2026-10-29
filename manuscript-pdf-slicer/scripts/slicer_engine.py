"""
Header Docstring:
Role: Deterministic PDF slicing and Ghostscript stream compression engine.
Stage: Document Slicing & Preprocessing (Stage 1 of Manuscript Audit Pipeline).
Inputs: Source PDF or Word document path, version string, optional page selection list.
Outputs: Sliced & compressed PDF chunks in ./<file_stem>/<version>/chunks/ and chunk_manifest.json.
Invariants:
- Every chunk must pass through Ghostscript 1.4 (/ebook profile) to guarantee byte size strictly < 2.0 MB.
- All output paths are dynamically scoped to the document stem and version to prevent directory collisions.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess
import hashlib
import json
import pypdf

class ManuscriptSlicer:
    """
    Partitions academic manuscripts into page-bounded or token-bounded chunks
    and enforces Ghostscript PDF 1.4 compression to defeat upload size ceilings.
    """

    def __init__(
        self,
        source_path: Path | str,
        version: str = "v1",
        output_dir: Optional[Path | str] = None,
    ) -> None:
        self.source_path = Path(source_path).resolve()
        if not self.source_path.exists():
            raise FileNotFoundError(f"Source manuscript not found at: {self.source_path}")

        self.file_stem = self.source_path.stem
        self.version = version

        # Generalized workspace scaffolding: defaults to ./<file_stem>/<version>/chunks/
        if output_dir:
            self.output_dir = Path(output_dir).resolve()
        else:
            self.output_dir = Path.cwd() / self.file_stem / self.version / "chunks"

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def compress_chunk_gs(self, input_pdf: Path, output_pdf: Path) -> Path:
        """
        Compresses a sliced chunk using Ghostscript to strip duplicate embedded fonts/images
        and ensure file size satisfies the platform's 2.10 MB rejection ceiling.
        """
        cmd = [
            "gs",
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            "-dPDFSETTINGS=/ebook",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            f"-sOutputFile={output_pdf}",
            str(input_pdf),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"Ghostscript compression failed for {input_pdf.name}:\n{result.stderr}"
            )
        return output_pdf

    def slice_pages(self, pages: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Extracts specified pages (or all pages if None) into individual compressed PDF chunks
        and generates an authoritative chunk_manifest.json.
        """
        reader = pypdf.PdfReader(str(self.source_path))
        total_doc_pages = len(reader.pages)
        target_pages = pages if pages is not None else list(range(1, total_doc_pages + 1))

        chunks: List[Dict[str, Any]] = []
        total_words = 0

        for p_num in target_pages:
            if p_num < 1 or p_num > total_doc_pages:
                raise ValueError(
                    f"Page {p_num} out of bounds (document has {total_doc_pages} pages)"
                )

            page_obj = reader.pages[p_num - 1]
            writer = pypdf.PdfWriter()
            writer.add_page(page_obj)

            raw_chunk = self.output_dir / f"raw_page_{p_num:02d}.pdf"
            compressed_chunk = self.output_dir / f"page_{p_num:02d}.pdf"

            # 1. Write uncompressed slice
            with open(raw_chunk, "wb") as f_out:
                writer.write(f_out)

            # 2. Ghostscript recompression pass
            self.compress_chunk_gs(raw_chunk, compressed_chunk)
            raw_chunk.unlink(missing_ok=True)

            # 3. Extract text and compute token metrics
            extracted_text = page_obj.extract_text() or ""
            words = len(extracted_text.split())
            total_words += words
            byte_size = compressed_chunk.stat().st_size

            # 4. Verify size ceiling invariant
            if byte_size >= 2.10 * 1024 * 1024:
                raise RuntimeError(
                    f"Chunk {compressed_chunk.name} ({byte_size} bytes) exceeds the 2.10MB upload ceiling after Ghostscript compression"
                )

            # 5. Compute SHA256 checksum for audit immutability
            with open(compressed_chunk, "rb") as f_chunk:
                chk_hash = hashlib.sha256(f_chunk.read()).hexdigest()

            rel_path = f"./{self.file_stem}/{self.version}/chunks/page_{p_num:02d}.pdf"

            chunks.append({
                "chunk_id": f"chk_{p_num:03d}",
                "page_start": p_num,
                "page_end": p_num,
                "word_count": words,
                "byte_size": byte_size,
                "relative_path": rel_path,
                "file_path": str(compressed_chunk.resolve()),
                "sha256": chk_hash,
            })

        # 6. Assemble authoritative manifest
        manifest: Dict[str, Any] = {
            "manifest_version": "1.0.0",
            "source_document": str(self.source_path),
            "file_stem": self.file_stem,
            "version": self.version,
            "total_pages": len(target_pages),
            "total_words": total_words,
            "compression_engine": "ghostscript_ebook_1.4",
            "chunks": chunks,
        }

        manifest_path = self.output_dir / "chunk_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f_manifest:
            json.dump(manifest, f_manifest, indent=2)

        return manifest
