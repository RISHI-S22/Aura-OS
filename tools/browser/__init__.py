from typing import Any, Dict, List

class UniversalBrowserPrimitive:
    """Extracts interactive accessibility elements from any arbitrary webpage."""

    @staticmethod
    def parse_interactive_nodes(accessibility_snapshot: Dict[str, Any]) -> List[Dict[str, str]]:
        nodes: List[Dict[str, str]] = []
        interactive_roles = {"button", "link", "textbox", "searchbox", "combobox", "menuitem", "checkbox"}

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
