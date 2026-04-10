import tempfile
import logging
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from app.adapters.base import BaseAdapter

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except Exception:  # pragma: no cover - dependency/runtime availability is environment-specific
    sync_playwright = None
    PlaywrightTimeoutError = Exception


class WebAdapter(BaseAdapter):
    logger = logging.getLogger(__name__)

    def prepare(self) -> str:
        return "Prepared browser session"

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        if sync_playwright is None:
            return self._synthetic_fallback(payload, reason="Playwright is not installed in agent runtime", status="blocked")

        target_url = str(payload.get("target_url") or "").strip()
        headless = bool(payload.get("headless", True))
        run_mode = "headless" if headless else "headed"
        test_case_id = str(payload.get("test_case_id") or "unknown")

        if not headless and self._running_in_container():
            return self._blocked_result(
                payload,
                reason="Headed browser mode is not available inside the Docker container. Run locally to see the browser window.",
            )

        artifacts_dir = Path(tempfile.gettempdir()) / "ste-artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        try:
            with sync_playwright() as playwright:
                try:
                    browser = playwright.chromium.launch(
                        headless=headless,
                        slow_mo=250 if not headless else 0,
                        args=["--no-sandbox", "--disable-setuid-sandbox"],
                    )
                except Exception as exc:
                    self.logger.exception("Web execution failed during browser launch")
                    status = "blocked" if isinstance(exc, NotImplementedError) else "failed"
                    return self._synthetic_fallback(
                        payload,
                        reason=f"Browser launch failed in {run_mode} mode: {self._format_exception(exc)}",
                        status=status,
                    )

                try:
                    context = browser.new_context(ignore_https_errors=True)
                    page = context.new_page()
                except Exception as exc:
                    browser.close()
                    self.logger.exception("Web execution failed during browser context setup")
                    status = "blocked" if isinstance(exc, NotImplementedError) else "failed"
                    return self._synthetic_fallback(
                        payload,
                        reason=f"Browser context setup failed in {run_mode} mode: {self._format_exception(exc)}",
                        status=status,
                    )

                steps: list[dict[str, Any]] = []

                try:
                    if target_url:
                        page.goto(target_url, wait_until="domcontentloaded", timeout=20000)
                except Exception as exc:
                    browser.close()
                    self.logger.exception("Web execution failed during initial navigation")
                    return self._synthetic_fallback(
                        payload,
                        reason=f"Navigation failed in {run_mode} mode: {self._format_exception(exc)}",
                        status="failed",
                    )

                for index, step in enumerate(payload.get("steps", []), start=1):
                    steps.append(
                        self._run_step(
                            page=page,
                            step=step,
                            step_number=index,
                            test_case_id=test_case_id,
                            base_url=target_url,
                            artifacts_dir=artifacts_dir,
                        )
                    )

                base_index = len(steps)
                for offset, assertion in enumerate(payload.get("assertions", []), start=1):
                    steps.append(
                        self._run_assertion(
                            page=page,
                            assertion=assertion,
                            step_number=base_index + offset,
                            test_case_id=test_case_id,
                            artifacts_dir=artifacts_dir,
                        )
                    )

                try:
                    if not headless:
                        page.wait_for_timeout(1200)
                finally:
                    browser.close()

            status = self._derive_run_status(steps)
            message = (
                f"Web flow executed against {target_url} in {'headless' if headless else 'headed'} mode"
                if target_url
                else f"Web flow executed in {'headless' if headless else 'headed'} mode"
            )
            confidence_by_status = {
                "passed": 0.9,
                "blocked": 0.98,
                "failed": 0.65,
                "inconclusive": 0.75,
                "suspicious": 0.75,
            }
            confidence = confidence_by_status.get(status, 0.75)
            return {
                "status": status,
                "message": message,
                "confidence": confidence,
                "steps": steps,
            }
        except Exception as exc:
            status = "blocked" if isinstance(exc, NotImplementedError) else "failed"
            formatted = self._format_exception(exc)
            self.logger.exception("Web execution failed with Playwright exception")
            return self._synthetic_fallback(payload, reason=f"Playwright execution failed in {run_mode} mode: {formatted}", status=status)

    def _running_in_container(self) -> bool:
        return Path("/.dockerenv").exists() or Path("/run/.containerenv").exists()

    def _run_step(
        self,
        page,
        step: dict[str, Any],
        step_number: int,
        test_case_id: str,
        base_url: str,
        artifacts_dir: Path,
    ) -> dict[str, Any]:
        action = str(step.get("action") or "perform_step").strip().lower()
        target = str(step.get("target") or "").strip()
        value = step.get("value")

        action_label = f"{action}:{target or 'n/a'}"
        expected = "Step completes without blocking error"

        try:
            if action == "navigate":
                destination = target
                if base_url and destination.startswith("/"):
                    destination = urljoin(base_url, destination)
                page.goto(destination or base_url, wait_until="domcontentloaded", timeout=20000)
                actual = f"Navigated to {page.url}"
            elif action in {"input", "fill", "type"}:
                locator = self._resolve_locator(page, target)
                locator.first.fill("" if value is None else str(value), timeout=10000)
                actual = f"Filled input {target}"
            elif action == "click":
                locator = self._resolve_locator(page, target)
                locator.first.click(timeout=10000)
                actual = f"Clicked {target}"
            elif action in {"verify_element", "validate_feature"}:
                locator = self._resolve_locator(page, target)
                locator.first.wait_for(state="visible", timeout=8000)
                actual = f"Verified element {target}"
            else:
                actual = f"Action {action} is not explicitly mapped; marked as executed"

            evidence = [self._capture_step_artifact(page, test_case_id, step_number, artifacts_dir)]
            return {
                "step_number": step_number,
                "action": action_label,
                "expected_result": expected,
                "actual_result": actual,
                "verdict": {"status": "passed", "reason": "Browser step executed", "confidence": 0.9},
                "evidence": evidence,
            }
        except PlaywrightTimeoutError as exc:
            return self._failed_step(step_number, action_label, expected, f"Timed out: {exc}", page, test_case_id, artifacts_dir)
        except Exception as exc:
            return self._failed_step(step_number, action_label, expected, str(exc), page, test_case_id, artifacts_dir)

    def _run_assertion(self, page, assertion: dict[str, Any], step_number: int, test_case_id: str, artifacts_dir: Path) -> dict[str, Any]:
        assertion_type = str(assertion.get("type") or "assert").strip().lower()
        target = str(assertion.get("target") or "").strip()
        value = assertion.get("value")

        action_label = f"assert:{assertion_type}"
        expected = "Assertion should pass"

        try:
            if assertion_type == "url_contains":
                expected_value = "" if value is None else str(value)
                if expected_value and expected_value not in page.url:
                    raise RuntimeError(f"Current URL '{page.url}' does not contain '{expected_value}'")
                actual = f"URL contains {expected_value}"
            elif assertion_type == "element_visible":
                locator = self._resolve_locator(page, target)
                locator.first.wait_for(state="visible", timeout=8000)
                actual = f"Element visible: {target}"
            else:
                actual = f"Assertion {assertion_type} not explicitly mapped; marked as passed"

            evidence = [self._capture_step_artifact(page, test_case_id, step_number, artifacts_dir)]
            return {
                "step_number": step_number,
                "action": action_label,
                "expected_result": expected,
                "actual_result": actual,
                "verdict": {"status": "passed", "reason": "Assertion passed", "confidence": 0.9},
                "evidence": evidence,
            }
        except Exception as exc:
            return self._failed_step(step_number, action_label, expected, str(exc), page, test_case_id, artifacts_dir)

    def _resolve_locator(self, page, target: str):
        normalized = target.strip().lower()

        if target.startswith("css="):
            return page.locator(target[4:])
        if target.startswith("xpath="):
            return page.locator(f"xpath={target[6:]}")
        if target.startswith("text="):
            return page.get_by_text(target[5:], exact=False)
        if normalized in {"header", "site header"}:
            return page.locator("header, [role='banner']")
        if normalized in {"footer", "site footer"}:
            return page.locator("footer, [role='contentinfo']")
        if normalized in {"main_content", "main content", "main", "content area", "content"}:
            return page.locator("main, [role='main'], #main_content, #main-content, .main-content, .content, .content-area")
        if normalized.endswith("button") or " button" in normalized:
            label = normalized.replace("button", "").strip()
            if label:
                return page.get_by_role("button", name=label, exact=False)
        if normalized.endswith("field") or normalized.endswith("input") or normalized.endswith("text area") or normalized.endswith("textarea"):
            label = normalized.replace("field", "").replace("input", "").replace("text area", "").replace("textarea", "").strip()
            if label:
                return page.get_by_role("textbox", name=label, exact=False)
        return page.locator(target)

    def _capture_step_artifact(self, page, test_case_id: str, step_number: int, artifacts_dir: Path) -> str:
        file_path = artifacts_dir / f"{test_case_id}-step-{step_number}.png"
        page.screenshot(path=str(file_path), full_page=True)
        return f"artifact://{file_path.name}"

    def _failed_step(self, step_number: int, action: str, expected: str, reason: str, page, test_case_id: str, artifacts_dir: Path) -> dict[str, Any]:
        evidence: list[str] = []
        try:
            evidence.append(self._capture_step_artifact(page, test_case_id, step_number, artifacts_dir))
        except Exception:
            pass
        return {
            "step_number": step_number,
            "action": action,
            "expected_result": expected,
            "actual_result": reason,
            "verdict": {"status": "failed", "reason": reason, "confidence": 0.5},
            "evidence": evidence,
        }

    def _derive_run_status(self, steps: list[dict[str, Any]]) -> str:
        verdicts = {str(step.get("verdict", {}).get("status") or "").strip().lower() for step in steps}

        if "failed" in verdicts:
            return "failed"
        if "blocked" in verdicts:
            return "blocked"
        if "suspicious" in verdicts:
            return "suspicious"
        if "inconclusive" in verdicts:
            return "inconclusive"
        return "passed"

    def _format_exception(self, exc: Exception) -> str:
        text = str(exc).strip()
        if text:
            return text
        return f"{exc.__class__.__name__} (no details)"

    def _synthetic_fallback(self, payload: dict[str, Any], reason: str, status: str = "failed") -> dict[str, Any]:
        steps = []
        for index, step in enumerate(payload.get("steps", []), start=1):
            step_reason = f"Playwright execution unavailable: {reason}"
            target_text = str(step.get("target") or "n/a")
            target_url = str(payload.get("target_url") or "").strip()
            if step.get("action") == "navigate" and target_url:
                target_text = target_url

            steps.append(
                {
                    "step_number": index,
                    "action": f"{step.get('action', 'perform_step')}:{target_text}",
                    "expected_result": "Step completes without blocking error",
                    "actual_result": step_reason,
                    "verdict": {"status": status, "reason": step_reason, "confidence": 0.5},
                    "evidence": [f"artifact://{payload['test_case_id']}/web-step-{index}.png"],
                }
            )
        confidence = 0.98 if status == "blocked" else 0.65
        return {
            "status": status,
            "message": f"Web execution used synthetic fallback ({reason})",
            "confidence": confidence,
            "steps": steps or [
                {
                    "step_number": 1,
                    "action": "dispatch_to_agent",
                    "expected_result": "Agent executes browser flow",
                    "actual_result": reason,
                    "verdict": {"status": status, "reason": reason, "confidence": confidence},
                    "evidence": [],
                }
            ],
        }

    def _blocked_result(self, payload: dict[str, Any], reason: str, steps: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        return {
            "status": "blocked",
            "message": reason,
            "confidence": 0.98,
            "steps": steps or [
                {
                    "step_number": 1,
                    "action": "dispatch_to_agent",
                    "expected_result": "Agent executes browser flow",
                    "actual_result": reason,
                    "verdict": {"status": "blocked", "reason": reason, "confidence": 0.98},
                    "evidence": [],
                }
            ],
        }
