from typing import Dict, Any

async def fetch_page_summary(url: str) -> Dict[str, Any]:
    \"\"\"Launches headless Chromium via Playwright to extract page title and visible text.\"\"\"
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"status": "unavailable", "reason": "playwright not installed", "url": url}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            title = await page.title()
            text = await page.locator("body").inner_text()
            return {
                "status": "success",
                "url": url,
                "title": title,
                "excerpt": text[:1500].strip(),
            }
        finally:
            await context.close()
            await browser.close()
