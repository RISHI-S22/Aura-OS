import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import agents
from core.planning.task_planner import planner
from core.orchestration.graph import aura_graph
from aura.security.approval import ApprovalGate
from memory.manager import memory_manager

app = FastAPI(
    title="AURA OS API",
    description="Autonomous Universal Reasoning Assistant Central Brain Endpoint",
    version="0.1.0"
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
        "error": None
    }
    
    final_state = aura_graph.invoke(initial_state)
    memory_manager.episodic.record(req.command, final_state["status"], final_state.get("artifacts", {}))

    return {
        "session_id": session_id,
        "intent": final_state["intent"],
        "plan": final_state["plan"],
        "status": final_state["status"]
    }

@app.post("/api/v1/approve")
def approve_action(req: ApprovalRequest):
    if ApprovalGate.approve(req.request_id):
        return {"status": "approved", "request_id": req.request_id}
    raise HTTPException(status_code=404, detail="Request ID not found")