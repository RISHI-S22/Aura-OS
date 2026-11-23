import asyncio
from agents.computer.action_planner import DesktopActionPlanner
from core.orchestration.dispatcher import dispatcher
from tools.computer import UniversalDesktopPrimitive

def test_discover_start_menu_apps_returns_dict():
    apps = UniversalDesktopPrimitive.discover_start_menu_apps()
    assert isinstance(apps, dict)

def test_action_planner_infers_launch_app_when_no_controls_present():
    planner = DesktopActionPlanner()
    decision = planner.decide_next_action(goal="Open Paint", controls=[], ocr_blocks=[])
    assert decision["action"] == "launch_app"
    assert decision["target_name"] == "Paint"

def test_desktop_agent_executes_launch_app_in_dry_run():
    res = asyncio.run(dispatcher.dispatch("desktop_agent", {"id": "app_1", "title": "Open Notepad"}))
    assert res["status"] == "success"
    trace = res["execution_trace"][0]
    assert trace["decision"]["action"] == "launch_app"
    assert trace["actuation"]["executed"] is True
