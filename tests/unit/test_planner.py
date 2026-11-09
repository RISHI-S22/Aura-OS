from core.planning.task_planner import create_plan

def test_research_and_spreadsheet_creates_ordered_tasks():
    result = create_plan("Research three AI companies and prepare a comparison spreadsheet")
    ids = [task["task_id"] for task in result["tasks"]]
    assert "research" in ids
    assert "verify" in ids
    assert "create_artifact" in ids
    artifact = next(task for task in result["tasks"] if task["task_id"] == "create_artifact")
    assert "verify" in artifact["depends_on"]

def test_email_requires_approval():
    result = create_plan("Research a company and email me the report")
    email = next(task for task in result["tasks"] if task["task_id"] == "send_message")
    assert email["requires_approval"] is True
