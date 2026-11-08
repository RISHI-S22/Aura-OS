"""
Aura-OS Autonomous Grounded Web Agent
Uses CDP (Chrome DevTools Protocol) over a dedicated debug port.
Prevents wrapper process termination, TargetClosedError, and profile locks.
"""

import asyncio
import json
import os
import subprocess
import sys
import time
import urllib.parse
import requests
from playwright.async_api import async_playwright

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import MODELS, PATHS

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
CDP_PORT = 9222
CDP_URL = f"http://127.0.0.1:{CDP_PORT}"

BROWSER_PATHS = [
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Opera GX\opera.exe"),
    os.path.expandvars(r"%PROGRAMFILES%\Opera GX\opera.exe"),
    os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
    os.path.expandvars(r"%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe"),
    os.path.expandvars(r"%PROGRAMFILES%\BraveSoftware\Brave-Browser\Application\brave.exe")
]

class UniversalWebAgent:
    def __init__(self, tts_callback=None):
        self.speak = tts_callback or (lambda text: print(f"[Aura Web]: {text}"))

    def get_browser_binary(self) -> str:
        for p in BROWSER_PATHS:
            if os.path.exists(p):
                return p
        return None

    def is_cdp_ready(self) -> bool:
        try:
            r = requests.get(f"{CDP_URL}/json/version", timeout=1.0)
            return r.status_code == 200
        except Exception:
            return False

    def launch_browser_daemon(self, browser_exe: str, user_data_dir: str):
        """Launches the user browser in normal execution mode exposing the debugging port."""
        if self.is_cdp_ready():
            return

        cmd = [
            browser_exe,
            f"--remote-debugging-port={CDP_PORT}",
            f"--user-data-dir={user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check"
        ]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Wait for CDP endpoint to become responsive
        for _ in range(15):
            time.sleep(0.5)
            if self.is_cdp_ready():
                return

    def deduce_start_destination(self, user_goal: str) -> tuple[str, str]:
        prompt = (
            f"Analyze this request: '{user_goal}'.\n"
            "Return JSON ONLY with this schema:\n"
            "{\n"
            "  \"target_url\": \"<exact URL, e.g. https://www.youtube.com, https://leetcode.com, https://www.flipkart.com>\",\n"
            "  \"search_query\": \"<search query to type once on that site, or null>\"\n"
            "}"
        )
        try:
            res = requests.post(OLLAMA_URL, json={
                "model": MODELS.LLM_MODEL,
                "prompt": prompt,
                "format": "json",
                "stream": False
            }, timeout=8).json()
            data = json.loads(res.get("response", "{}"))
            target_url = data.get("target_url")
            search_query = data.get("search_query")
            if target_url and target_url.startswith("http"):
                return target_url, search_query
        except Exception:
            pass

        # Fallback query
        clean = user_goal.lower()
        for w in ["hi aura", "aura", "open opera gx", "open opera", "open browser", "in that"]:
            clean = clean.replace(w, "")
        return f"https://duckduckgo.com/?q={urllib.parse.quote_plus(clean.strip())}", None

    async def execute_task(self, natural_query: str):
        browser_exe = self.get_browser_binary()
        if not browser_exe:
            self.speak("Could not locate an installed browser binary.")
            return

        user_data_dir = os.path.join(PATHS.WORKSPACE, "browser_profile")
        os.makedirs(user_data_dir, exist_ok=True)

        self.speak("Connecting to web environment.")
        self.launch_browser_daemon(browser_exe, user_data_dir)

        async with async_playwright() as p:
            try:
                browser = await p.chromium.connect_over_cdp(CDP_URL)
            except Exception as e:
                self.speak("Failed to attach to browser debugging interface.")
                print(f"[!] CDP Connection Error: {e}")
                return

            context = browser.contexts[0] if browser.contexts else await browser.new_context()

            # Ensure we attach to an active, valid tab
            page = None
            for p_curr in context.pages:
                if not p_curr.is_closed():
                    page = p_curr
                    break
            if not page:
                page = await context.new_page()

            start_url, search_query = self.deduce_start_destination(natural_query)
            clean_host = urllib.parse.urlparse(start_url).netloc
            self.speak(f"Navigating to {clean_host or 'destination'}.")

            try:
                await page.goto(start_url, wait_until="domcontentloaded", timeout=20000)
            except Exception:
                try:
                    await page.goto(start_url, wait_until="commit", timeout=10000)
                except Exception as e:
                    print(f"[!] Navigation notice: {e}")

            await asyncio.sleep(2.5)

            # Autonomous Sense-Reason-Act Loop
            max_steps = 10
            for step in range(max_steps):
                if page.is_closed():
                    # Reacquire tab if user or site redirected into a new tab
                    pages = [p for p in context.pages if not p.is_closed()]
                    if not pages:
                        break
                    page = pages[-1]

                interactive_elements = await self.index_interactive_elements(page)

                context_summary = await page.evaluate("""
                    () => {
                        const title = document.title || '';
                        const bodyText = document.body ? document.body.innerText.substring(0, 1000) : '';
                        return title + ' | ' + bodyText;
                    }
                """)

                plan = self.reason_next_step(natural_query, context_summary, interactive_elements)
                action = plan.get("action", "DONE").upper()

                if action == "DONE":
                    self.speak(plan.get("summary", "Task completed."))
                    break

                elif action == "CLICK":
                    elem_id = plan.get("id")
                    label = plan.get("label", "element")
                    self.speak(f"Clicking {label}.")
                    clicked = await self.click_indexed_element(page, elem_id)
                    if not clicked and label:
                        try:
                            await page.locator(f"text={label}").first.click(timeout=3000)
                        except Exception:
                            pass
                    await asyncio.sleep(3.0)

                elif action == "TYPE":
                    elem_id = plan.get("id")
                    text_val = plan.get("text", "")
                    press_enter = plan.get("press_enter", False)
                    self.speak("Entering input.")
                    await self.type_indexed_element(page, elem_id, text_val, press_enter)
                    await asyncio.sleep(2.5)

                elif action == "CODE_INJECT":
                    code_val = plan.get("code", "")
                    self.speak("Injecting code solution.")
                    await self.inject_editor_code(page, code_val)
                    await asyncio.sleep(2.0)

                elif action == "KEY":
                    key_val = plan.get("key", "Enter")
                    await page.keyboard.press(key_val)
                    await asyncio.sleep(2.0)

                elif action == "WAIT":
                    await asyncio.sleep(3.0)

    async def index_interactive_elements(self, page) -> list:
        try:
            return await page.evaluate("""
                () => {
                    const elements = [];
                    const interactives = document.querySelectorAll(
                        'button, a, input, textarea, select, [role="button"], [role="link"], [contenteditable="true"], .monaco-editor, .cm-content'
                    );

                    let id = 1;
                    for (let el of interactives) {
                        const rect = el.getBoundingClientRect();
                        const style = window.getComputedStyle(el);

                        if (rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none') {
                            el.setAttribute('data-aura-id', id);
                            let label = el.innerText || el.value || el.placeholder || el.getAttribute('aria-label') || el.getAttribute('title') || '';
                            label = label.replace(/\\s+/g, ' ').trim().substring(0, 40);

                            elements.push({
                                id: id,
                                tag: el.tagName.toLowerCase(),
                                type: el.type || '',
                                label: label
                            });
                            id++;
                            if (id > 45) break;
                        }
                    }
                    return elements;
                }
            """)
        except Exception:
            return []

    def reason_next_step(self, user_goal: str, context_summary: str, elements: list) -> dict:
        elements_str = "\n".join([f"[{e['id']}] <{e['tag']}> {e['label']}" for e in elements if e['label']])

        prompt = (
            f"You are an autonomous web agent executing a user goal.\n"
            f"Goal: '{user_goal}'\n"
            f"Page Summary: {context_summary[:500]}\n\n"
            f"Interactive Elements on Screen:\n"
            f"{elements_str}\n\n"
            "Determine the single next atomic step.\n"
            "Return JSON ONLY with ONE of these schemas:\n"
            "- To click: {\"action\": \"CLICK\", \"id\": <element_id_number>, \"label\": \"<text_of_element>\"}\n"
            "- To type: {\"action\": \"TYPE\", \"id\": <element_id_number>, \"text\": \"<text_to_type>\", \"press_enter\": <true/false>}\n"
            "- To inject code: {\"action\": \"CODE_INJECT\", \"code\": \"<complete code string>\"}\n"
            "- To press a key: {\"action\": \"KEY\", \"key\": \"Enter\" | \"Space\"}\n"
            "- To wait: {\"action\": \"WAIT\"}\n"
            "- When finished: {\"action\": \"DONE\", \"summary\": \"<spoken summary>\"}"
        )
        try:
            res = requests.post(OLLAMA_URL, json={
                "model": MODELS.LLM_MODEL,
                "prompt": prompt,
                "format": "json",
                "stream": False
            }, timeout=25).json()
            return json.loads(res.get("response", "{}"))
        except Exception:
            return {"action": "DONE", "summary": "Task processing complete."}

    async def click_indexed_element(self, page, elem_id: int) -> bool:
        try:
            loc = page.locator(f"[data-aura-id='{elem_id}']").first
            if await loc.count() > 0:
                await loc.scroll_into_view_if_needed()
                await loc.click(timeout=4000)
                return True
        except Exception:
            pass
        return False

    async def type_indexed_element(self, page, elem_id: int, text: str, press_enter: bool = False):
        try:
            loc = page.locator(f"[data-aura-id='{elem_id}']").first
            if await loc.count() > 0:
                await loc.scroll_into_view_if_needed()
                await loc.click(timeout=3000)
                await loc.fill(text)
                if press_enter:
                    await loc.press("Enter")
        except Exception:
            await page.keyboard.insert_text(text)
            if press_enter:
                await page.keyboard.press("Enter")

    async def inject_editor_code(self, page, code: str):
        injected = await page.evaluate("""
            (code) => {
                if (window.monaco && window.monaco.editor) {
                    const eds = window.monaco.editor.getEditors();
                    if (eds.length > 0) { eds[0].setValue(code); return true; }
                }
                const cm5 = document.querySelector('.CodeMirror');
                if (cm5 && cm5.CodeMirror) { cm5.CodeMirror.setValue(code); return true; }
                if (window.ace) {
                    const aceEl = document.querySelector('.ace_editor');
                    if (aceEl && window.ace.edit(aceEl)) { window.ace.edit(aceEl).setValue(code); return true; }
                }
                return false;
            }
        """, code)

        if not injected:
            target = page.locator(".cm-content, .monaco-editor, .ace_editor, textarea").first
            if await target.count() > 0:
                await target.click()
                await page.keyboard.press("Control+A")
                await page.keyboard.press("Backspace")
                await page.keyboard.insert_text(code)