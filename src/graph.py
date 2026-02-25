# automation-auditor/src/graph.py
from langgraph.graph import StateGraph, END
from .state import AgentState

def start(state: AgentState) -> AgentState:
    """
    Smoke test node that simply passes the state through.
    """
    print("--- Entering Start Node ---")
    return state

def build_graph():
    """
    Builds and compiles the Automaton Auditor LangGraph.
    """
    # Initialize the StateGraph with our Pydantic AgentState
    builder = StateGraph(AgentState)
    
    # Add nodes
    builder.add_node("start", start)
    
    # Define edges
    builder.set_entry_point("start")
    builder.add_edge("start", END)
    
    # Compile the graph
    app = builder.compile()
    
    return app
