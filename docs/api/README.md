# AURA OS API Reference

## Endpoints

### GET /api/v1/health
Returns service health and active system version.

### POST /api/v1/commands
Submits a natural language command to the cognitive planner and LangGraph execution engine.

### GET /api/v1/history
Retrieves recent episodic command executions.

### POST /api/v1/approve
Authorizes a paused action waiting at the security approval gate.

### WS /ws/telemetry
Real-time WebSocket stream broadcasting agent state transitions and execution progress.
