# automation-auditor/src/graph.py
from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes.detectives import repo_investigator_node, doc_analyst_node, vision_inspector_node
from .nodes.judges import prosecutor_node, defense_node, techlead_node
from .nodes.justice import chief_justice_node

def start(state: AgentState) -> AgentState:
    """
    Initial pass-through node for setup or smoke testing.
    """
    print("--- Auditor Swarm Starting ---")
    return state

def repo_investigator(state: AgentState) -> AgentState:
    print("--- Running RepoInvestigator ---")
    return repo_investigator_node(state)

def doc_analyst(state: AgentState) -> AgentState:
    print("--- Running DocAnalyst ---")
    return doc_analyst_node(state)

def vision_inspector(state: AgentState) -> AgentState:
    return vision_inspector_node(state)

def evidence_aggregator(state: AgentState) -> AgentState:
    print("--- Aggregating Forensic Evidence ---")
    return state

def prosecutor(state: AgentState) -> AgentState:
    return prosecutor_node(state)

def defense(state: AgentState) -> AgentState:
    return defense_node(state)

def tech_lead(state: AgentState) -> AgentState:
    return techlead_node(state)

def chief_justice(state: AgentState) -> AgentState:
    return chief_justice_node(state)

def build_graph():
    """
    Builds and compiles the Automaton Auditor LangGraph with parallel detective and judge orchestration.
    """
    builder = StateGraph(AgentState)
    
    # Add nodes
    builder.add_node("start", start)
    builder.add_node("repo_investigator", repo_investigator)
    builder.add_node("doc_analyst", doc_analyst)
    builder.add_node("vision_inspector", vision_inspector)
    builder.add_node("evidence_aggregator", evidence_aggregator)
    
    builder.add_node("prosecutor", prosecutor)
    builder.add_node("defense", defense)
    builder.add_node("tech_lead", tech_lead)
    
    builder.add_node("chief_justice", chief_justice)
    
    builder.set_entry_point("start")
    
    # Parallel Detectives
    builder.add_edge("start", "repo_investigator")
    builder.add_edge("start", "doc_analyst")
    builder.add_edge("start", "vision_inspector")
    
    # Fan-in Detectives to Aggregator
    builder.add_edge("repo_investigator", "evidence_aggregator")
    builder.add_edge("doc_analyst", "evidence_aggregator")
    builder.add_edge("vision_inspector", "evidence_aggregator")
    
    # Parallel Judges
    builder.add_edge("evidence_aggregator", "prosecutor")
    builder.add_edge("evidence_aggregator", "defense")
    builder.add_edge("evidence_aggregator", "tech_lead")
    
    # Fan-in Judges to Chief Justice
    builder.add_edge("prosecutor", "chief_justice")
    builder.add_edge("defense", "chief_justice")
    builder.add_edge("tech_lead", "chief_justice")
    
    # End
    builder.add_edge("chief_justice", END)
    
    # Compile the graph
    app = builder.compile()
    
    return app
