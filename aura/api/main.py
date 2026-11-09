from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from core.orchestration.graph import aura_graph
from core.verification.result_validator import validate_pipeline_result

app = FastAPI(
    title="AURA OS API",
    description="AURA cognitive planning foundation — milestone 1",
    version="0.1.0",
)

class CommandRequest(BaseModel):
    command: str = Field(min_length=3, max_length=5000)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "aura-api", "mode": "dry_run"}

@app.post("/api/v1/commands")
async def submit_command(request: CommandRequest):
    try:
        state = aura_graph.invoke({"command": request.command})
        verification = validate_pipeline_result(state)
        return {
            "command": request.command,
            "intent": state.get("intent"),
            "plan": state.get("plan", []),
            "execution_log": state.get("execution_log", []),
            "verification": verification,
            "response": state.get("response"),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Aura pipeline failed: {type(exc).__name__}")
