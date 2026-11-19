from typing import Any, Dict
from aura.voice.stt import SpeechToText
from aura.voice.tts import TextToSpeech
from core.orchestration.graph import aura_graph
from core.planning.task_planner import planner

class VoiceConversationEngine:
    """Connects STT input and TTS output directly to AURA cognitive orchestration."""

    def __init__(self):
        self.stt = SpeechToText()
        self.tts = TextToSpeech()

    async def process_text_utterance(self, transcript: str) -> Dict[str, Any]:
        plan_result = planner.plan(transcript)
        initial_state = {
            "command": transcript,
            "intent": plan_result.intent,
            "plan": [t.model_dump() for t in plan_result.subtasks],
            "current_step": 0,
            "artifacts": {},
            "approval_needed": False,
            "status": "planned",
            "error": None,
        }
        final_state = await aura_graph.ainvoke(initial_state)
        spoken_reply = self.tts.format_spoken_summary(
            status=final_state["status"],
            intent=final_state["intent"],
            step_count=len(final_state["plan"]),
        )
        return {
            "transcript": transcript,
            "spoken_reply": spoken_reply,
            "status": final_state["status"],
            "plan": final_state["plan"],
            "artifacts": final_state.get("artifacts", {}),
        }
