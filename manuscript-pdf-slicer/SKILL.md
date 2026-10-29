---
name: manuscript-pdf-slicer
version: 1.0.0
description: >-
  Partition academic PDF and Word manuscripts into upload-safe, token-bounded chunks
  with automated Ghostscript /ebook PDF 1.4 stream compression to defeat platform file
  size limits (<2.10MB). Auto-scaffolds standardized workspaces and outputs typed
  chunk_manifest.json schemas.
author: auto-edgecompute
tags:
  - academic-writing
  - pdf-processing
  - ghostscript
  - preprocessing
  - skillsmp
metadata:
  skillsmp_engine_version: "2.0"
  runtime_requirements:
    python: ">=3.10"
    binaries:
      - gs
    dependencies:
      - pypdf
      - pydantic
license: MIT
---

# Manuscript PDF Slicer

Use this skill to **partition, compress, and tokenize academic manuscripts** before running automated browser-based AI detection or downstream gate evaluations.

Naive page-extraction tools (`pypdf`, `pymupdf`) retain shared document-level XObject images, embedded fonts, and vector streams when carving out individual pages. A single 1-page PDF extracted from an academic thesis often balloons to **5.8 MB**, causing immediate rejection on browser upload portals (such as Grammarly's **2.10 MB** ceiling). 

This skill guarantees that every sliced chunk is stripped of duplicate font streams and recompressed via Ghostscript 1.4 (`/ebook` profile) down to **20 KB – 450 KB**, strictly below all upload ceilings, while recording page bounds, token metrics, and cryptographic hashes in an authoritative `chunk_manifest.json`.

---

## When to Activate

- When preparing an academic manuscript (`.pdf` or `.docx`) for automated AI score auditing via `ai-detector-auditor`.
- In a fresh or empty directory when receiving any arbitrary document.
- When platform file uploads fail with `"File exceeds 2.10 MB"` or `"File size too large"`.
- When an upstream gate requires chunk-level token counts and word-frequency distributions.

---

## Workspace Auto-Scaffolding Invariant

When provided with any source file (e.g., `thesis.pdf` or `docs/manuscript.pdf`), the skill automatically isolates its work into a **Document-Centric, Versioned Workspace**:

```
./<file_stem>/
└── <version>/                  # Defaults to v1
    └── chunks/
        ├── page_01.pdf         # Compressed (<500KB)
        ├── page_02.pdf
        └── chunk_manifest.json
```

**Rule**: Never write chunk files directly to root folders, flat temporary directories, or arbitrary locations. Always anchor output inside `./<file_stem>/<version>/chunks/`.

---

## Input Prerequisites (Establish First)

Before slicing, establish:
1. **Source File (`--source`)**: Absolute or relative path to the manuscript file.
2. **Version Tag (`--version`)**: Iteration identifier (default: `v1`).
3. **Target Pages (`--pages`)**: Specific page range (e.g. `1-5,8,11-14`), or omit to slice all pages.

---

## Execution Pattern

Execute strictly via Python module syntax (`-m`) using the workspace virtual environment:

```bash
# Slice all pages of thesis.pdf into v1 workspace
./.venv/bin/python -m scripts.manuscript_slicer.cli --source ./thesis.pdf --version v1

# Slice specific subset of pages (e.g. pages 8 to 14)
./.venv/bin/python -m scripts.manuscript_slicer.cli --source ./thesis.pdf --version v1 --pages 8-14
```

---

## Core Methodology & Ghostscript Compression

Raw extracted PDF pages are immediately piped through Ghostscript:

```bash
gs -sDEVICE=pdfwrite \
   -dCompatibilityLevel=1.4 \
   -dPDFSETTINGS=/ebook \
   -dNOPAUSE -dQUIET -dBATCH \
   -sOutputFile=./<file_stem>/<version>/chunks/page_01.pdf \
   ./<file_stem>/<version>/chunks/raw_page_01.pdf
```

### Invariants:
- **Hard Ceiling**: Byte size must be strictly $< 2{,}097{,}152$ bytes ($< 2.0$ MB).
- **Text Layer Preservation**: Slicing must preserve selectable text and ligature encoding.
- **Checksum Integrity**: Each chunk must have its SHA256 recorded in the manifest.

---

## Output Manifest Specification (`chunk_manifest.json`)

Saved automatically to `./<file_stem>/<version>/chunks/chunk_manifest.json`:

```json
{
  "manifest_version": "1.0.0",
  "source_document": "./thesis.pdf",
  "file_stem": "thesis",
  "version": "v1",
  "total_pages": 22,
  "total_words": 14210,
  "compression_engine": "ghostscript_ebook_1.4",
  "chunks": [
    {
      "chunk_id": "chk_001",
      "page_start": 1,
      "page_end": 1,
      "word_count": 512,
      "byte_size": 284120,
      "relative_path": "./thesis/v1/chunks/page_01.pdf",
      "file_path": "/workspace/thesis/v1/chunks/page_01.pdf",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    }
  ]
}
```

---

## Anti-Patterns

- **Raw PyPDF Slicing Without Ghostscript**: Submitting uncompressed raw slices to upload platforms will trigger intermittent $>2.10$ MB upload rejections.
- **Hardcoding Output Paths**: Never hardcode machine-specific paths like `/home/user/...`. Rely on relative workspace scoping.
- **Mutating Source Files**: Slicing is strictly read-only on the input manuscript.
- **Arbitrary Token Slicing Across Sentences**: Never cut text mid-sentence; keep slices anchored to structural page or paragraph boundaries.

---

## Related Skills

- `ai-detector-auditor`: Downstream consumer; reads `chunk_manifest.json` and audits each chunk.
- `stubborn-humanizer`: Downstream remediator; takes high-scoring chunks identified during audit and produces updated document versions (`v2`).
