---
name: ai-detector-auditor
version: 1.0.0
description: >-
  Parallel, verifiable AI detection auditor for academic PDF and Word manuscripts.
  Orchestrates arbitrary N-worker Chrome GUI sessions with geometry tiling, handles
  native upload button actionability bypass, enforces strict visible-digit regex gating
  (^\d{1,3}%$) against false-zero errors, captures screenshot proof galleries, and
  consolidates simple and word-weighted average scorecards. Mandates real Google Chrome
  and GUI mode (headless=False ALWAYS).
author: auto-edgecompute
tags:
  - academic-writing
  - ai-detection
  - audit
  - playwright
  - quality-assurance
  - skillsmp
metadata:
  skillsmp_engine_version: "2.0"
  runtime_requirements:
    python: ">=3.10"
    dependencies:
      - playwright
      - pypdf
      - pydantic
license: MIT
---

# AI Detector Auditor

Use this skill to run **automated, verifiable AI detection audits** across partitioned manuscript chunks, extracting proof screenshots and authoritative simple and word-weighted scorecards.

---

## Mandatory Chrome GUI Mode (`headless=False` ALWAYS)

> [!IMPORTANT]
> **Strict GUI Invariant**: All AI detection audits MUST run with real Google Chrome (`channel="chrome"`) and **GUI Mode Enabled (`headless=False` ALWAYS)**.
> 
> Running in headless mode (`headless=True`) is **strictly forbidden** because:
> 1. **Bot Detection & Cloudflare**: Web application firewalls and platform bot-detection mechanisms immediately restrict or flag headless Chromium instances.
> 2. **React DOM Hydration Failure**: The React score meter DOM element often fails to transition from placeholder dashes (`-`) to digits in headless contexts, causing false-zero or infinite loading stalls.
> 3. **Verifiable Visual Proof**: Real-time visual observability is essential so the operator can inspect the visible score meter circle on the screen.

### How to Enable and Configure Chrome GUI Mode

1. **Google Chrome Channel & Launch Configuration**:
   Playwright must launch using the installed system Google Chrome binary with geometry tiling:
   ```python
   browser = p.chromium.launch(
       channel="chrome",
       headless=False,  # ALWAYS False!
       args=[
           "--no-sandbox",
           "--disable-setuid-sandbox",
           f"--window-position={x_pos},{y_pos}",
           "--window-size=1280,900",
       ],
       env=os.environ.copy(),  # Forwards display sockets
   )
   ```

2. **Display Sockets (WSLg / Linux / X11)**:
   Ensure the following environment variables are active in your shell:
   - **WSLg (Windows Subsystem for Linux GUI)**:
     ```bash
     export DISPLAY=:0
     export WAYLAND_DISPLAY=wayland-0
     export XDG_RUNTIME_DIR=/mnt/wslg/runtime-dir
     ```
   - **Native Linux / X11**:
     ```bash
     export DISPLAY=:0
     ```
   The auditor script automatically copies `os.environ` to ensure Playwright inherits these display sockets without crashing or disappearing into a background headless socket.

3. **Multi-Worker Geometry Tiling**:
   Parallel workers automatically compute non-overlapping screen offsets:
   - **Worker 1**: `--window-position=0,0`
   - **Worker 2**: `--window-position=640,0`
   - **Worker 3**: `--window-position=0,450`
   - **Worker 4**: `--window-position=640,450`

---

## When to Activate

- After slicing a manuscript with `manuscript-pdf-slicer`.
- When an author requires certified AI percentage scorecards with screenshot proof.
- When evaluating the effectiveness of a humanization pass by comparing scores between `v1` and `v2`.
- When scanning specific pages (e.g. abstract, methodology, results) for compliance.

---

## Workspace Auto-Scaffolding Invariant

The auditor automatically scopes all runtime traces, proof screenshots, and final reports inside the document-centric hierarchy:

```
./<file_stem>/
└── <version>/
    ├── chunks/                         # Reads chunk_manifest.json
    └── ai-score/                       # Auto-scaffolded output directory
        ├── screenshots/                # Visual verification gallery
        │   ├── page_01_0pct.png
        │   └── page_08_38pct.png
        ├── scan_session_manifest.json  # Raw telemetry & retry counts
        ├── audit_summary.json          # Simple & word-weighted statistics
        └── audit_report.md             # Markdown scorecard with clickable proofs
```

---

## Input Prerequisites (Establish First)

Before starting the audit, verify:
1. **Manifest Path (`--manifest`)** or **Document Stem (`--file-stem`)** and **Version (`--version`)**: Points to `./<file_stem>/<version>/chunks/chunk_manifest.json`.
2. **Worker Concurrency (`--workers`)**: Number of parallel Chrome browser contexts ($1 \le N \le 8$, default: 2).
3. **GUI Visibility**: Guaranteed by default (`headless=False` ALWAYS).

---

## Execution Pattern

Execute strictly via Python module syntax (`-m`) using the workspace virtual environment:

```bash
# Standard Execution: 2-worker audit with visible Chrome GUI tiling (headless=False)
./.venv/bin/python -m scripts.ai_detector_auditor.cli --file-stem thesis --version v1 --workers 2

# Explicit manifest path execution (headless=False is default)
./.venv/bin/python -m scripts.ai_detector_auditor.cli --manifest ./thesis/v1/chunks/chunk_manifest.json --workers 2
```

---

## Core Verification Invariants

### 1. The Anti-False-Zero Invariant
- **Rule**: Never record `0%` unless the meter explicitly renders visible digits matching `^\d{1,3}%$` AND the network API response confirms `0.0`.
- **Handling**: If the meter remains `-` or empty, the engine re-clicks "Scan for AI" up to 15 times with 6–8s polling intervals.

### 2. Actionability Bypass & State Hydration
- **Rule**: Native file upload button must be clicked with `force=True`.
- **Rule**: After file chooser sets files, enforce a mandatory **3.5-second hydration pause** before clicking "Scan for AI" to allow the React state machine to bind document buffers.

### 3. Display Preservation (WSLg / X11)
- Subprocess runners must inherit `env=os.environ` containing `WAYLAND_DISPLAY`, `XDG_RUNTIME_DIR`, and `DISPLAY` to prevent socket crashes.

---

## Output Manifests & Mathematics

### Mathematical Metrics
$$\bar{S}_{\text{simple}} = \frac{1}{M}\sum_{i=1}^M S_i \qquad \bar{S}_{\text{weighted}} = \frac{\sum_{i=1}^M (S_i \times W_i)}{\sum_{i=1}^M W_i}$$

### `audit_summary.json`
Saved at: `./<file_stem>/<version>/ai-score/audit_summary.json`:
```json
{
  "document_name": "thesis.pdf",
  "file_stem": "thesis",
  "version": "v1",
  "total_chunks_scanned": 22,
  "total_words_evaluated": 14210,
  "simple_average_score": 6.68,
  "weighted_average_score": 8.86,
  "zero_detection_count": 11,
  "zero_detection_percentage": 50.0,
  "max_score_chunk": {
    "chunk_id": "chk_008",
    "page_start": 8,
    "score": 38,
    "screenshot_path": "./thesis/v1/ai-score/screenshots/page_08_38pct.png"
  }
}
```

---

## Anti-Patterns

- **Headless Mode (`headless=True`)**: Never run in headless mode. Headless runs trigger platform bot defenses, fail React DOM animations, and prevent real-time verification of visible percentage digits. Keep `headless=False` ALWAYS.
- **Pasting Text Into Contenteditable**: Never paste text directly into DOM textareas; this drops formatting, triggers platform rate limits, and produces false score spikes. Always use native file upload (`expect_file_chooser`).
- **Treating Missing Digits as Zero**: Never parse `""`, `"-"`, or `"Scan"` as zero percent.
- **Reporting Simple Average Alone**: Never report only the arithmetic mean; always report both simple and word-weighted averages.
- **Unstructured Global Screenshot Dumps**: Never save screenshots to root `temp/`. Strictly enforce `./<file_stem>/<version>/ai-score/screenshots/`.

---

## Related Skills

- `manuscript-pdf-slicer`: Upstream generator; provides `chunk_manifest.json`.
- `stubborn-humanizer`: Downstream remediator; triggered when chunks score above the target threshold (e.g. $>15\%$).
