from core.planning.task_planner import CognitivePlanner

def test_research_and_spreadsheet_creates_ordered_tasks():
    planner = CognitivePlanner()
    plan = planner._heuristic_fallback("Research three AI companies and prepare a comparison spreadsheet")
    assert len(plan.subtasks) >= 2
    assert plan.subtasks[0].agent == "research_agent"
    assert plan.subtasks[1].agent == "document_agent"
    assert "task_1" in plan.subtasks[1].dependencies

def test_email_requires_approval():
    planner = CognitivePlanner()
    plan = planner._heuristic_fallback("Send an email to the professor")
    email_tasks = [t for t in plan.subtasks if t.agent == "email_agent"]
    assert len(email_tasks) == 1
    assert email_tasks[0].requires_approval is True
