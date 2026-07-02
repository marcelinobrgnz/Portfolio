"""Capture full portfolio screenshots of the Streamlit chat with Q&A proof."""
from __future__ import annotations

import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "portfolio"
URL = "http://localhost:8501"
QUESTION = "How many weeks of parental leave do employees get?"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1600, "height": 1000},
            device_scale_factor=2,
        )
        page = context.new_page()
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_selector("text=SecureGuard RAG", timeout=30000)

        # Fresh question for a clean chat state.
        chat = page.get_by_placeholder("Ask about company policies...")
        chat.click()
        chat.fill(QUESTION)
        chat.press("Enter")

        page.wait_for_selector("text=26 weeks", timeout=90000)
        time.sleep(1.5)

        # Expand Sources and scroll it into view.
        page.get_by_text("Sources", exact=True).first.click()
        time.sleep(0.8)
        source_line = page.locator("code, pre, [data-testid='stCode']").filter(
            has_text="s3://"
        )
        if source_line.count() > 0:
            source_line.first.scroll_into_view_if_needed()
            time.sleep(0.5)

        page.screenshot(
            path=str(OUT / "secureguard-rag-full.png"),
            full_page=True,
        )
        page.screenshot(
            path=str(OUT / "secureguard-rag-viewport.png"),
            full_page=False,
        )

        browser.close()

    print(f"Saved: {OUT / 'secureguard-rag-full.png'}")
    print(f"Saved: {OUT / 'secureguard-rag-viewport.png'}")


if __name__ == "__main__":
    main()
