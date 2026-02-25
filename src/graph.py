# automation-auditor/src/graph.py
from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes.detectives import repo_investigator_node, doc_analyst_node

def start(state: AgentState) -> AgentState:
    """
    Initial pass-through node for setup or smoke testing.
    """
    print("--- Auditor Swarm Starting ---")
    return state

def repo_investigator(state: AgentState) -> AgentState:
    """
    Wrapper for the RepoInvestigator forensic tool.
    """
    print("--- Running RepoInvestigator ---")
    return repo_investigator_node(state)

def doc_analyst(state: AgentState) -> AgentState:
    """
    Wrapper for the DocAnalyst forensic tool.
    """
    print("--- Running DocAnalyst ---")
    return doc_analyst_node(state)

def evidence_aggregator(state: AgentState) -> AgentState:
    """
    Fan-in point to synchronize detective findings before future judicial analysis.
    Currently a pass-through node for the interim milestone.
    """
    print("--- Aggregating Forensic Evidence ---")
    return state

def build_graph():
    """
    Builds and compiles the Automaton Auditor LangGraph with detective orchestration.
    """
    # Initialize the StateGraph with our Pydantic AgentState
    builder = StateGraph(AgentState)
    
    # Add nodes
    builder.add_node("start", start)
    builder.add_node("repo_investigator", repo_investigator)
    builder.add_node("doc_analyst", doc_analyst)
    builder.add_node("evidence_aggregator", evidence_aggregator)
    
    # Define edges (Sequential orchestration for interim simplicity)
    builder.set_entry_point("start")
    
    builder.add_edge("start", "repo_investigator")
    builder.add_edge("repo_investigator", "doc_analyst")
    builder.add_edge("doc_analyst", "evidence_aggregator")
    builder.add_edge("evidence_aggregator", END)
    
    # Compile the graph
    app = builder.compile()
    
    return app
