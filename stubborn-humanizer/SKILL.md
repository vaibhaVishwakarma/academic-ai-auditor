---
name: stubborn-humanizer
version: 1.0.0
description: >-
  Multi-tier cascading humanization engine for resistant academic prose. Injects Stage 0
  heuristic typographic and syntactic variance (arrow normalization, em-dash stripping,
  sparse parenthesis spacing, active/passive voice shifting), enforces automated 2-strike
  verification gating, and coordinates Stage 2 micro-chunk token slicing (<180 words)
  with JSON HITL candidate resolution and v2 workspace branching.
author: auto-edgecompute
tags:
  - academic-writing
  - humanization
  - syntax-refactoring
  - hitl
  - skillsmp
metadata:
  skillsmp_engine_version: "2.0"
  runtime_requirements:
    python: ">=3.10"
    dependencies:
      - pydantic
license: MIT
---

# Stubborn Humanizer

Use this skill to **systematically remediate stubborn, high-scoring AI text passages** identified during an audit without altering scientific assertions, numerical data, or citations.

Academic prose generated or polished by LLMs exhibits distinct statistical signatures: uniform sentence cadence, excessive em-dashes (`—`), and predictable transitions (*"Furthermore"*, *"Moreover"*).

This skill applies a **3-stage cascading workflow**:
1. **Stage 0 (Heuristic Typographic & Syntactic Variance)**: Inverts passive/active sentence structures, eliminates em-dashes, standardizes pseudo-ASCII arrows, and injects human typographical spacing within parentheses.
2. **Stage 1 (Automated 2-Strike Verification Gating)**: Re-audits mutated candidates through `ai-detector-auditor`. Candidates achieving $\le 15\%$ AI score pass immediately; those failing 2 consecutive strikes escalate.
3. **Stage 2 (Micro-Chunk Token Slicing & JSON HITL Escalation)**: For stubborn passages exceeding 2 strikes or auxiliary tool input limits (<200 words on tools like `aihumanizer.io`), the skill slices text into $<180$-word micro-chunks, orchestrates multi-variant rewriting, and produces a structured candidate manifest for human-in-the-loop (HITL) resolution.

---

## When to Activate

- When `ai-detector-auditor` reports chunk or page scores exceeding the target threshold (e.g. $>15\%$) in `./<file_stem>/<version>/ai-score/audit_summary.json`.
- When specific sections exhibit stubborn AI patterns resisting naive edits.
- When an author requires systematic elimination of AI-tells across a manuscript.

---

## Workspace Auto-Scaffolding Invariant

The humanizer scopes all mutated candidates and remediation records into:

```
./<file_stem>/
├── v1/
│   ├── chunks/
│   ├── ai-score/                       # Identifies chunks with score > 15%
│   └── humanized/                      # Auto-scaffolded remediation directory
│       ├── candidates/
│       ├── humanizer_manifest.json     # Mutated candidates & strike records
│       └── <file_stem>_v1_humanized.docx
└── v2/                                 # Auto-branched for the re-audit cycle
    ├── chunks/
    └── ai-score/
```

---

## Input Prerequisites (Establish First)

Before starting humanization, establish:
1. **Document Stem (`--file-stem`)**: Document identifier (e.g. `thesis`).
2. **Baseline Version (`--version`)**: Iteration containing audit failures (default: `v1`).
3. **Score Threshold (`--threshold`)**: Maximum acceptable score (default: `15`).

---

## Execution Pattern

Execute strictly via Python module syntax (`-m`) using the workspace virtual environment:

```bash
# Remediate all chunks above 15% in v1 and branch to v2
./.venv/bin/python -m scripts.stubborn_humanizer.cli --file-stem thesis --version v1 --threshold 15
```

---

## Heuristic Mutation Taxonomy (Stage 0 Rules)

| Rule ID | Transformation | Rationale |
| :--- | :--- | :--- |
| **H-01 (Dash Elimination)** | Replace em-dashes (`—`), en-dashes (`–`), and `--` with commas, parenthetical clauses, or distinct sentences. | Em-dashes are one of the strongest statistical markers of modern LLM prose. |
| **H-02 (Arrow Normalization)** | `<--` $\to$ `<-`, `==>` $\to$ `->`. | Detectors flag malformed pseudo-ASCII symbols as unnatural syntax. |
| **H-03 (Parenthesis Spacing)** | Inject sparse, human-like spacing: `( xyz )`, `( xyz)`, `(xyz )`. | Disrupts token transition probabilities modeled by n-gram detectors. |
| **H-04 (Conjunction Variance)**| Sparsely alternate between `&` and `and`. | Natural academic prose contains idiosyncratic typographical shortcuts. |
| **H-05 (Voice Inversion)** | Invert passive clauses to active or split compound-complex sentences. | Breaks the characteristic monotonous sentence-length distribution of LLMs. |

---

## Output Manifest Specification (`humanizer_manifest.json`)

Saved to `./<file_stem>/<version>/humanized/humanizer_manifest.json`:

```json
{
  "manifest_version": "1.0.0",
  "file_stem": "thesis",
  "version": "v1",
  "threshold": 15,
  "total_chunks_remediated": 1,
  "remediations": [
    {
      "chunk_id": "chk_008",
      "page_number": 8,
      "baseline_ai_score": 38,
      "target_threshold": 15,
      "status": "IN_REMEDIATION",
      "candidates": [
        {
          "candidate_id": "cand_01",
          "stage": 0,
          "strike_number": 1,
          "text": "The edge scheduler dynamically reallocates microservices based on telemetry ( CPU, memory, and network queues ).",
          "word_count": 16,
          "verified_score": null,
          "status": "PENDING_VERIFICATION"
        }
      ]
    }
  ]
}
```

---

## Anti-Patterns

- **Thesaurus Synonym Substitution**: Replacing technical terms with obscure synonyms damages academic clarity and rarely lowers AI scores.
- **Payload Token Overflow**: Submitting more than 180 words to auxiliary web tools causes HTTP 400 errors. Always partition into micro-chunks before sending.
- **Scattering Output Files Across Flat Folders**: Never output humanized chunks into root directories. Confine everything strictly inside `./<file_stem>/<version>/humanized/`.
- **Declaring Victory Without Re-Audit**: Never assume a humanized paragraph passed without running a re-audit through `ai-detector-auditor` on the new `v2` manuscript.

---

## Related Skills

- `ai-detector-auditor`: Upstream trigger; provides `scan_session_manifest.json`.
- `manuscript-pdf-slicer`: Downstream processor; slices newly compiled `v2` manuscript for re-auditing.
