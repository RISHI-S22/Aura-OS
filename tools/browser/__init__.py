from typing import Any, Dict, List, Optional

class UniversalBrowserPrimitive:
    """General-purpose browser perception and action primitive using accessibility trees."""

    @staticmethod
    def parse_interactive_nodes(accessibility_snapshot: Dict[str, Any]) -> List[Dict[str, str]]:
        nodes: List[Dict[str, str]] = []
        interactive_roles = {
            "button", "link", "textbox", "searchbox",
            "combobox", "menuitem", "checkbox", "tab",
        }

        def walk(node: Dict[str, Any]):
            if not isinstance(node, dict):
                return
            role = str(node.get("role", "")).lower()
            name = str(node.get("name", "")).strip()
            if role in interactive_roles and name:
                nodes.append({"role": role, "name": name})
            for child in node.get("children", []):
                walk(child)

        walk(accessibility_snapshot)
        return nodes

    async def execute_browser_action(
        self,
        url: Optional[str] = None,
        role: Optional[str] = None,
        name: Optional[str] = None,
        action: str = "inspect",
        text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Executes generic ARIA-role interactions on any live webpage via Playwright."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return {"status": "skipped", "reason": "playwright not installed in environment"}

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            if url:
                await page.goto(url, wait_until="domcontentloaded")
            if action == "click" and role and name:
                await page.get_by_role(role, name=name).first.click()
            elif action == "fill" and role and name and text is not None:
                await page.get_by_role(role, name=name).first.fill(text)
            snapshot = await page.accessibility.snapshot() or {}
            title = await page.title()
            await browser.close()
            return {
                "status": "success",
                "title": title,
                "interactive_elements": self.parse_interactive_nodes(snapshot)[:25],
            }
