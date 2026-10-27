"""LangGraph wiring for the photo-upload pipeline: Verifier runs first,
then Resolver decides based on its output. Triggered by POST /deals/{id}/photo
(see backend/routes/deals.py)."""

from typing import TypedDict

from langgraph.graph import END, StateGraph

from agents import resolver, verifier


class GraphState(TypedDict, total=False):
    deal_id: str
    verifier_result: dict
    resolver_result: dict


def _run_verifier(state: GraphState) -> dict:
    return {"verifier_result": verifier.verify(state["deal_id"])}


def _run_resolver(state: GraphState) -> dict:
    return {"resolver_result": resolver.decide(state["deal_id"], state["verifier_result"])}


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("verifier", _run_verifier)
    graph.add_node("resolver", _run_resolver)
    graph.set_entry_point("verifier")
    graph.add_edge("verifier", "resolver")
    graph.add_edge("resolver", END)
    return graph.compile()


_compiled_graph = None


def run_verification_pipeline(deal_id: str) -> dict:
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    final_state = _compiled_graph.invoke({"deal_id": deal_id})
    return final_state["resolver_result"]
