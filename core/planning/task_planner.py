from core.cognition.intent_classifier import classify_intent
from core.planning.task_decomposer import decompose_command

def create_plan(command: str) -> dict:
    intent = classify_intent(command)
    tasks = decompose_command(command, intent.category)
    return {
        "intent": {
            "category": intent.category,
            "confidence": intent.confidence,
            "requires_external_action": intent.requires_external_action,
        },
        "tasks": [
            {
                "task_id": task.task_id,
                "description": task.description,
                "agent": task.agent,
                "depends_on": list(task.depends_on),
                "requires_approval": task.requires_approval,
                "status": "planned",
            }
            for task in tasks
        ],
    }
