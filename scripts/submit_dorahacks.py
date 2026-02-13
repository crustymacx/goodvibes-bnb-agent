#!/usr/bin/env python3
"""Submit placeholder BUIDL to DoraHacks Good Vibes Only hackathon via Playwright."""

import asyncio
import sys

async def main():
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)  # Visible so Jon can watch/intervene
        context = await browser.new_context()
        page = await context.new_page()

        print("[1/5] Navigating to DoraHacks hackathon page...")
        await page.goto("https://dorahacks.io/hackathon/goodvibes", timeout=30000)
        await page.wait_for_load_state("networkidle")

        # Take a screenshot so we can see current state
        await page.screenshot(path="/tmp/dorahacks_1_landing.png")
        print("[1/5] Screenshot saved to /tmp/dorahacks_1_landing.png")

        # Check if already logged in
        page_content = await page.content()
        if "Sign In" in page_content or "Login" in page_content:
            print("[!] Not logged in. Jon needs to log in via browser first.")
            print("    Opening login page...")
            await page.goto("https://dorahacks.io/login", timeout=30000)
            await page.screenshot(path="/tmp/dorahacks_login.png")
            print("    Screenshot: /tmp/dorahacks_login.png")
            print("    Please log in manually, then re-run this script.")
            await browser.close()
            return

        print("[2/5] Looking for Submit BUIDL button...")
        # Try to find and click Submit BUIDL
        submit_btn = page.locator("text=Submit BUIDL").first
        if await submit_btn.is_visible():
            await submit_btn.click()
            await page.wait_for_load_state("networkidle")
            await page.screenshot(path="/tmp/dorahacks_2_submit.png")
            print("[2/5] Clicked Submit BUIDL. Screenshot: /tmp/dorahacks_2_submit.png")
        else:
            # Try alternative selectors
            alt_btns = ["text=Submit", "text=Register", "text=Apply", "[data-testid='submit']"]
            for sel in alt_btns:
                btn = page.locator(sel).first
                if await btn.is_visible():
                    await btn.click()
                    break
            await page.wait_for_load_state("networkidle")
            await page.screenshot(path="/tmp/dorahacks_2_submit.png")
            print("[2/5] Screenshot: /tmp/dorahacks_2_submit.png")

        print("[3/5] Filling in BUIDL form...")
        # The form fields vary — take a screenshot and report what we see
        await page.screenshot(path="/tmp/dorahacks_3_form.png")
        print("[3/5] Form screenshot: /tmp/dorahacks_3_form.png")
        print("       Current URL:", page.url)

        # Print page structure for debugging
        inputs = await page.locator("input, textarea, select").all()
        print(f"       Found {len(inputs)} form fields")
        for inp in inputs[:10]:
            name = await inp.get_attribute("name") or await inp.get_attribute("placeholder") or "?"
            print(f"         - {name}")

        await browser.close()
        print("\n[Done] Screenshots saved. Check /tmp/dorahacks_*.png")

if __name__ == "__main__":
    asyncio.run(main())
