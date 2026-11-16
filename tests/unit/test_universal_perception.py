import asyncio
import agents  # noqa: F401
from core.orchestration.dispatcher import dispatcher

def test_browser_agent_perceives_arbitrary_accessibility_tree():
    snapshot = {
        "role": "WebArea",
        "name": "Example Portal",
        "children": [
            {"role": "searchbox", "name": "Search query"},
            {"role": "button", "name": "Submit"},
            {"role": "generic", "name": "Decorative wrapper"},
        ],
    }
    task = {"id": "b1", "title": "Search portal", "ui_snapshot": snapshot}
    res = asyncio.run(dispatcher.dispatch("browser_agent", task))
    assert res["status"] == "success"
    assert res["perceived_elements_count"] == 2
    assert res["interactive_elements"][0]["role"] == "searchbox"

def test_desktop_agent_filters_actionable_os_controls():
    controls = [
        {"control_type": "Edit", "name": "Editor", "is_enabled": True},
        {"control_type": "Button", "name": "Save", "is_enabled": True},
        {"control_type": "Button", "name": "DisabledBtn", "is_enabled": False},
        {"control_type": "Pane", "name": "Background", "is_enabled": True},
    ]
    task = {"id": "d1", "title": "Interact with app", "ui_controls": controls}
    res = asyncio.run(dispatcher.dispatch("desktop_agent", task))
    assert res["status"] == "success"
    assert res["actionable_controls_count"] == 2
