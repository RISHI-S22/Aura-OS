import uuid
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import agents  # noqa: F401
from aura.security.approval import ApprovalGate
from core.orchestration.graph import aura_graph
from core.planning.task_planner import planner
from memory.manager import memory_manager

app = FastAPI(
    title="AURA OS API",
    description="Autonomous Universal Reasoning Assistant Central Brain Endpoint",
    version="0.1.0",
)

class CommandRequest(BaseModel):
    command: str

class ApprovalRequest(BaseModel):
    request_id: str

@app.get("/health")
@app.get("/api/v1/health")
def health_check():
    return {"status": "online", "system": "AURA-OS", "version": "0.1.0"}

@app.post("/api/v1/commands")
async def execute_command(req: CommandRequest):
    if not req.command.strip():
        raise HTTPException(status_code=400, detail="Command cannot be empty")

    session_id = str(uuid.uuid4())[:8]
    plan_result = planner.plan(req.command)

    initial_state = {
        "command": req.command,
        "intent": plan_result.intent,
        "plan": [t.model_dump() for t in plan_result.subtasks],
        "current_step": 0,
        "artifacts": {},
        "approval_needed": False,
        "status": "planned",
        "error": None,
    }

    final_state = aura_graph.invoke(initial_state)
    memory_manager.episodic.record(
        session_id=session_id,
        command=req.command,
        status=final_state["status"],
        artifacts=final_state.get("artifacts", {}),
    )

    return {
        "session_id": session_id,
        "intent": final_state["intent"],
        "plan": final_state["plan"],
        "artifacts": final_state.get("artifacts", {}),
        "status": final_state["status"],
    }

@app.get("/api/v1/history")
def get_history(limit: int = 10):
    return {"episodes": memory_manager.episodic.recent(limit)}

@app.post("/api/v1/approve")
def approve_request(req: ApprovalRequest):
    if ApprovalGate.approve(req.request_id):
        return {"status": "approved", "request_id": req.request_id}
    raise HTTPException(status_code=404, detail="Approval request not found")