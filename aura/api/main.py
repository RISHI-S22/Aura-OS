import uuid
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import agents  # noqa: F401
from agents.base.agent_registry import agent_registry
from aura.integrations.mcp import mcp_registry
from aura.security.approval import ApprovalGate
from aura.voice.conversation import VoiceConversationEngine
from core.orchestration.dispatcher import dispatcher
from core.orchestration.graph import aura_graph, execute_node
from core.planning.dependency_graph import DependencyGraph
from core.planning.task_planner import planner
from core.verification.action_checker import ActionChecker
from memory.manager import memory_manager

app = FastAPI(
    title="AURA OS API",
    description="Autonomous Universal Reasoning Assistant Central Brain Endpoint",
    version="0.5.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

voice_engine = VoiceConversationEngine()

class CommandRequest(BaseModel):
    command: str
    live_mode: bool = False

class ApprovalRequest(BaseModel):
    request_id: str

@app.get("/health")
@app.get("/api/v1/health")
def health_check():
    return {"status": "online", "system": "AURA-OS", "version": "0.5.0"}

@app.get("/api/v1/capabilities")
def get_capabilities():
    return {
        "agents": list(agent_registry._agents.keys()),
        "mcp_tools": mcp_registry.list_tools(),
    }

@app.get("/api/v1/memory/procedures")
def get_learned_procedures(q: str = "", limit: int = 10):
    return {"procedures": memory_manager.procedural.recall(q, limit=limit)}

@app.post("/api/v1/commands")
async def execute_command(req: CommandRequest):
    if not req.command.strip():
        raise HTTPException(status_code=400, detail="Command cannot be empty")

    session_id = str(uuid.uuid4())[:8]
    plan_result = planner.plan(req.command)
    subtasks = []
    for t in plan_result.subtasks:
        d = t.model_dump()
        d["live_os"] = req.live_mode
        subtasks.append(d)

    initial_state = {
        "command": req.command,
        "intent": plan_result.intent,
        "plan": subtasks,
        "current_step": 0,
        "artifacts": {},
        "approval_needed": False,
        "status": "planned",
        "error": None,
    }

    final_state = await aura_graph.ainvoke(initial_state)
    if final_state["status"] == "pending_approval":
        ApprovalGate.create_request(session_id, req.command, final_state)
    elif final_state["status"] == "completed":
        for res in final_state.get("artifacts", {}).values():
            if isinstance(res, dict) and res.get("execution_trace"):
                memory_manager.procedural.record_procedure(
                    goal=req.command,
                    agent=res.get("agent", "unknown"),
                    action_sequence=res["execution_trace"],
                )

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

@app.post("/api/v1/sessions/{session_id}/resume")
async def resume_session(session_id: str):
    saved_state = ApprovalGate.get_payload(session_id)
    if not saved_state:
        raise HTTPException(status_code=404, detail="Suspended session not found")

    ApprovalGate.approve(session_id)
    resumed_state = dict(saved_state)
    step = resumed_state.get("current_step", 0)
    plan = [dict(t) for t in resumed_state.get("plan", [])]
    if step < len(plan):
        plan[step]["requires_approval"] = False
    resumed_state["plan"] = plan
    resumed_state["approval_needed"] = False

    final_state = await execute_node(resumed_state)
    memory_manager.episodic.record(
        session_id=session_id,
        command=resumed_state.get("command", ""),
        status=final_state["status"],
        artifacts=final_state.get("artifacts", {}),
    )
    return {
        "session_id": session_id,
        "status": final_state["status"],
        "artifacts": final_state.get("artifacts", {}),
    }

@app.post("/api/v1/voice/utterance")
async def execute_voice_utterance(req: CommandRequest):
    if not req.command.strip():
        raise HTTPException(status_code=400, detail="Transcript cannot be empty")
    return await voice_engine.process_text_utterance(req.command)

@app.websocket("/ws/commands")
async def websocket_command_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            payload = await websocket.receive_json()
            command = str(payload.get("command", "")).strip()
            live_mode = bool(payload.get("live_mode", False))
            if not command:
                await websocket.send_json({"event": "error", "detail": "Empty command"})
                continue

            session_id = str(uuid.uuid4())[:8]
            plan_obj = planner.plan(command)
            subtasks = []
            for t in plan_obj.subtasks:
                d = t.model_dump()
                d["live_os"] = live_mode
                subtasks.append(d)

            dag = DependencyGraph()
            for t in subtasks:
                dag.add_node(t["id"], t.get("dependencies", []))
            id_map = {t["id"]: t for t in subtasks}
            ordered = [id_map[tid] for tid in dag.topological_sort()]

            await websocket.send_json({
                "event": "planned",
                "session_id": session_id,
                "intent": plan_obj.intent,
                "plan": ordered,
            })

            artifacts = {}
            halted = False
            for idx, task in enumerate(ordered):
                if task.get("requires_approval"):
                    ApprovalGate.create_request(
                        session_id,
                        command,
                        {
                            "command": command,
                            "intent": plan_obj.intent,
                            "plan": ordered,
                            "current_step": idx,
                            "artifacts": artifacts,
                            "approval_needed": True,
                            "status": "pending_approval",
                        },
                    )
                    await websocket.send_json({
                        "event": "pending_approval",
                        "session_id": session_id,
                        "task": task,
                    })
                    halted = True
                    break

                await websocket.send_json({
                    "event": "step_started",
                    "session_id": session_id,
                    "task_id": task["id"],
                    "agent": task["agent"],
                })
                task["context"] = {d: artifacts[d] for d in task.get("dependencies", []) if d in artifacts}
                res = await dispatcher.dispatch(task["agent"], task)
                verified = ActionChecker.verify_step(task, res)
                artifacts[task["id"]] = res
                await websocket.send_json({
                    "event": "step_verified" if verified else "step_failed",
                    "session_id": session_id,
                    "task_id": task["id"],
                    "result": res,
                })

            if not halted:
                memory_manager.episodic.record(session_id, command, "completed", artifacts)
                await websocket.send_json({
                    "event": "completed",
                    "session_id": session_id,
                    "artifacts": artifacts,
                })
    except WebSocketDisconnect:
        pass

@app.get("/api/v1/history")
def get_history(limit: int = 10):
    return {"episodes": memory_manager.episodic.recent(limit)}

@app.post("/api/v1/approve")
def approve_request(req: ApprovalRequest):
    if ApprovalGate.approve(req.request_id):
        return {"status": "approved", "request_id": req.request_id}
    raise HTTPException(status_code=404, detail="Approval request not found")
