"""
Aura-OS Playwright Browser Agent
Inspects DOM elements, automates web applications, and controls media playback
via Chrome DevTools Protocol (CDP) or isolated browser instances.
"""

import asyncio
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from playwright.async_api import async_playwright

class BrowserAgent:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None

    async def initialize(self, headless: bool = False):
        p = await async_playwright().start()
        self.browser = await p.chromium.launch(headless=headless, args=["--start-maximized"])
        self.context = await self.browser.new_context(no_viewport=True)
        self.page = await self.context.new_page()

    async def play_youtube_video(self, query: str):
        if not self.page:
            await self.initialize(headless=False)

        encoded = query.replace(" ", "+")
        await self.page.goto(f"https://www.youtube.com/results?search_query={encoded}")
        await self.page.wait_for_selector("ytd-video-renderer", timeout=10000)

        # Click the first video title link directly in the DOM
        first_video = self.page.locator("ytd-video-renderer #video-title").first
        await first_video.click()

    async def toggle_media_playback(self):
        """Executes JavaScript inside the active page to pause/play any HTML5 video tag."""
        if self.page:
            await self.page.evaluate("""
                () => {
                    const video = document.querySelector('video');
                    if (video) {
                        video.paused ? video.play() : video.pause();
                    }
                }
            """)

    async def close(self):
        if self.browser:
            await self.browser.close()