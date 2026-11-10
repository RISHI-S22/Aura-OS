from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import agents
from core.planning.task_planner import planner
from core.orchestration.graph import aura_graph

app = FastAPI(
    title="AURA OS API",
    description="Autonomous Universal Reasoning Assistant Central Brain Endpoint",
    version="0.1.0"
)

class CommandRequest(BaseModel):
    command: str

class CommandResponse(BaseModel):
    intent: str
    plan: List[Dict[str, Any]]
    status: str

@app.get("/health")
@app.get("/api/v1/health")
def health_check():
    return {"status": "online", "system": "AURA-OS", "version": "0.1.0"}

@app.post("/api/v1/commands", response_model=CommandResponse)
async def execute_command(req: CommandRequest):
    if not req.command.strip():
        raise HTTPException(status_code=400, detail="Command cannot be empty")

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

    return CommandResponse(
        intent=final_state["intent"],
        plan=final_state["plan"],
        status=final_state["status"]
    )
