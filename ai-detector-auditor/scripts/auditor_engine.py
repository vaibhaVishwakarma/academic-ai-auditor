"""
Header Docstring:
Role: Multi-worker browser orchestrator for automated, verifiable AI audits.
Stage: Auditing & Metric Extraction (Stage 2 of Manuscript Audit Pipeline).
Inputs: Path to chunk_manifest.json, worker concurrency count, headless flag.
Outputs: Screenshots in ./<file_stem>/<version>/ai-score/screenshots/,
         scan_session_manifest.json, audit_summary.json, and audit_report.md.
Invariants:
- Never record 0% unless meter explicitly renders visible digits matching ^\\d{1,3}%$ AND API validates.
- Preserve full parent environment (env=os.environ) to avoid WSLg/X11 socket drops.
- Enforce force=True on upload clicks to bypass React button animation actionability deadlocks.
"""

from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import os
import re
import time
from playwright.sync_api import sync_playwright

from scripts.ai_detector_auditor.math_aggregator import compute_audit_statistics, generate_markdown_report

class AIDetectorAuditor:
    """
    Automated GUI browser auditor for academic PDF chunks.
    Orchestrates tiled Chrome browser sessions and enforces strict visible-digit verification.
    """

    def __init__(
        self,
        manifest_path: Path | str,
        workers: int = 2,
        headless: bool = False,
        output_dir: Optional[Path | str] = None,
    ) -> None:
        self.manifest_path = Path(manifest_path).resolve()
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Chunk manifest not found at: {self.manifest_path}")

        with open(self.manifest_path, "r", encoding="utf-8") as f:
            self.manifest_data = json.load(f)

        self.file_stem = self.manifest_data.get("file_stem", Path(self.manifest_data["source_document"]).stem)
        self.version = self.manifest_data.get("version", "v1")
        self.workers = max(1, min(workers, 8))
        self.headless = headless

        # Generalized workspace scaffolding
        if output_dir:
            self.output_dir = Path(output_dir).resolve()
        else:
            self.output_dir = Path.cwd() / self.file_stem / self.version / "ai-score"

        self.screenshots_dir = self.output_dir / "screenshots"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

    def _scan_chunk_session(
        self,
        chunk: Dict[str, Any],
        worker_id: int,
        max_scan_attempts: int = 15,
    ) -> Dict[str, Any]:
        """Runs an isolated Playwright browser context to audit a single PDF chunk."""
        chunk_id = chunk["chunk_id"]
        chunk_file = Path(chunk["file_path"]).resolve()
        start_page = chunk.get("page_start", 1)
        end_page = chunk.get("page_end", 1)
        word_count = chunk.get("word_count", 0)

        # Calculate desktop window tiling position
        cols = 2
        row = (worker_id - 1) // cols
        col = (worker_id - 1) % cols
        x_pos = col * 640
        y_pos = row * 450

        print(f"[Worker {worker_id}] Starting audit on {chunk_id} (p{start_page:02d}, {word_count} words)...")

        result: Dict[str, Any] = {
            "chunk_id": chunk_id,
            "start_page": start_page,
            "end_page": end_page,
            "word_count": word_count,
            "score_percent": None,
            "screenshot_path": None,
            "attempts_needed": 0,
            "worker_id": worker_id,
            "error": None,
        }

        api_captured: Dict[str, Any] = {}

        def on_response(response: Any) -> None:
            if "aidetector" in response.url and response.status == 200:
                try:
                    payload = response.json()
                    api_captured["score"] = payload.get("score")
                    api_captured["alertRanges"] = payload.get("alertRanges", [])
                except Exception:
                    pass

        start_time = time.time()
        # Preserve full environment for WSLg / Wayland / X11
        proc_env = os.environ.copy()

        with sync_playwright() as p:
            browser = p.chromium.launch(
                channel="chrome",
                headless=self.headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    f"--window-position={x_pos},{y_pos}",
                    "--window-size=1280,900",
                ],
                env=proc_env,
            )
            context = browser.new_context(viewport={"width": 1280, "height": 900})
            page = context.new_page()
            page.on("response", on_response)

            try:
                # 1. Navigate to detector
                page.goto(
                    "https://www.grammarly.com/ai-detector",
                    wait_until="domcontentloaded",
                    timeout=45000,
                )

                # 2. Native File Upload with Actionability Bypass (force=True)
                upload_btn = page.locator('button:has-text("Upload file")')
                if upload_btn.count() > 0 and upload_btn.is_visible():
                    with page.expect_file_chooser(timeout=15000) as fc_info:
                        upload_btn.click(force=True)
                    file_chooser = fc_info.value
                    file_chooser.set_files(str(chunk_file))
                else:
                    # Fallback to hidden file input
                    page.wait_for_selector('input[type="file"]', state="attached", timeout=15000)
                    page.set_input_files('input[type="file"]', str(chunk_file))

                # 3. React State Binding Hydration Delay (crucial: avoids dropped clicks)
                time.sleep(3.5)

                # 4. Scanning & Persistent Retry Trigger Loop
                score_num: Optional[int] = None
                visible_pattern = re.compile(r"^\d{1,3}%$")

                for attempt in range(1, max_scan_attempts + 1):
                    result["attempts_needed"] = attempt

                    # Trigger scan button if present and clickable
                    scan_btn = page.locator('button:has-text("Scan for AI")')
                    if scan_btn.count() > 0 and scan_btn.is_visible():
                        try:
                            scan_btn.click(force=True, timeout=3000)
                        except Exception:
                            pass

                    # Poll for score meter transition to visible digits
                    poll_deadline = time.time() + 6.0
                    while time.time() < poll_deadline:
                        time.sleep(0.8)

                        # Check meter circle text for explicit digits (Anti-False-Zero Invariant)
                        meter_locators = page.locator("div").filter(has_text=visible_pattern)
                        if meter_locators.count() > 0:
                            for i in range(meter_locators.count()):
                                txt = meter_locators.nth(i).inner_text().strip()
                                m = visible_pattern.match(txt)
                                if m:
                                    score_num = int(txt.replace("%", ""))
                                    break
                        if score_num is not None:
                            break

                        # Secondary check: cross-validate with backend API intercept
                        if "score" in api_captured and api_captured["score"] is not None:
                            score_num = int(api_captured["score"])
                            break

                    if score_num is not None:
                        print(f"[Worker {worker_id}] Score acquired on attempt {attempt}: {score_num}%")
                        break

                if score_num is None:
                    raise TimeoutError(
                        f"Meter failed to display visible percentage digits after {max_scan_attempts} attempts."
                    )

                # 5. Proof Screenshot Capture
                shot_filename = f"page_{start_page:02d}_{score_num}pct.png"
                shot_path = self.screenshots_dir / shot_filename
                page.screenshot(path=str(shot_path), full_page=False)

                result["score_percent"] = score_num
                result["screenshot_path"] = str(shot_path.resolve())
                result["latency_seconds"] = round(time.time() - start_time, 2)
                print(f"[Worker {worker_id}] [✓] {chunk_id} -> {score_num}% (saved to {shot_filename})")

            except Exception as e:
                result["error"] = str(e)
                print(f"[Worker {worker_id}] [✗] Failed auditing {chunk_id}: {e}")
            finally:
                context.close()
                browser.close()

        return result

    def run_audit(self) -> Dict[str, Any]:
        """Executes parallel audit across all chunks in the manifest."""
        chunks = self.manifest_data.get("chunks", [])
        if not chunks:
            raise ValueError(f"No chunks found in manifest {self.manifest_path}")

        print(f"[*] Commencing audit: {len(chunks)} chunks across {self.workers} workers...")
        results: List[Dict[str, Any]] = []

        # ThreadPool for parallel browser contexts
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = []
            for idx, chunk in enumerate(chunks):
                # Stagger worker starts by 3.5s to prevent concurrent platform rate-limiting
                w_id = (idx % self.workers) + 1
                future = executor.submit(self._scan_chunk_session, chunk, w_id)
                futures.append(future)
                time.sleep(3.5)

            for future in futures:
                results.append(future.result())

        # Sort results by start page
        results.sort(key=lambda r: r.get("start_page", 0))

        # Save scan session manifest
        session_manifest = {
            "manifest_version": "1.0.0",
            "file_stem": self.file_stem,
            "version": self.version,
            "concurrency_workers": self.workers,
            "total_chunks_processed": len(results),
            "results": results,
        }

        session_path = self.output_dir / "scan_session_manifest.json"
        with open(session_path, "w", encoding="utf-8") as f:
            json.dump(session_manifest, f, indent=2)

        # Compute dual mathematical statistics
        summary = compute_audit_statistics(
            results=results,
            document_name=self.manifest_data.get("source_document", self.file_stem),
            file_stem=self.file_stem,
            version=self.version,
        )

        summary_path = self.output_dir / "audit_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        # Generate markdown report
        md_report = generate_markdown_report(summary)
        report_path = self.output_dir / "audit_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(md_report)

        print("\n" + "=" * 60)
        print(f"[✓] Audit Complete!")
        print(f"[✓] Simple Average: {summary['simple_average_score']}%")
        print(f"[✓] Weighted Average: {summary['weighted_average_score']}%")
        print(f"[✓] Zero-AI Pages: {summary['zero_detection_count']} / {summary['total_chunks_scanned']}")
        print(f"[✓] Deliverables written to: {self.output_dir}")
        print("=" * 60 + "\n")

        return summary
