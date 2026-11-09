from langgraph.graph import StateGraph, END
from core.orchestration.state import AuraState
from core.orchestration.supervisor import understand_and_plan, dispatch_tasks, build_response

def build_aura_graph():
    graph = StateGraph(AuraState)
    graph.add_node("understand_and_plan", understand_and_plan)
    graph.add_node("dispatch", dispatch_tasks)
    graph.add_node("respond", build_response)
    graph.set_entry_point("understand_and_plan")
    graph.add_edge("understand_and_plan", "dispatch")
    graph.add_edge("dispatch", "respond")
    graph.add_edge("respond", END)
    return graph.compile()

aura_graph = build_aura_graph()
