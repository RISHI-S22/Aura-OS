# AURA Core — Milestone 1

This is the first executable foundation for Aura's cognitive pipeline:
**command → intent → plan → dispatch → verification → response**.

It is deliberately model-agnostic. The initial planner uses transparent rules so the pipeline can be tested without API keys. A model provider can be added behind `core/model_router` in the next milestone.

## Requirements
- Python 3.11 or newer (Python 3.12 recommended)
- A virtual environment

## Install (PowerShell, from the Aura-OS repository root)
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
```

## Run the API
```powershell
uvicorn aura.api.main:app --reload
```
Open `http://127.0.0.1:8000/docs`.

## Test
```powershell
pytest
```

## Example request
POST `/api/v1/commands`
```json
{"command":"Research three AI companies and prepare a comparison spreadsheet"}
```

The current milestone creates and verifies a structured task plan. It does **not** yet browse the internet, create spreadsheets, send emails, or operate the desktop. Those capabilities will be connected through permissioned tools in later milestones.

## Safety boundary
The dispatcher is intentionally a dry-run planner. It does not execute shell commands, access files, send messages, or make external changes. Do not remove this boundary until each tool has a permission policy, sandbox and audit trail.
