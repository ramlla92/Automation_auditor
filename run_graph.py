# automation-auditor/run_graph.py
import json
from src.graph import build_graph
from src.state import AgentState
from src.config import init_tracing

def main():
    # 1. Initialize Tracing
    init_tracing()
    
    # 2. Build the Graph
    app = build_graph()
    
    # 3. Create initial state
    initial_state = AgentState(
        github_urls=["https://github.com/example/repo"],
        pdf_path="report.pdf"
    )
    
    # 4. Invoke the app
    # Note: For Pydantic models in StateGraph, we pass instances
    print("--- Invoking LangGraph ---")
    final_state_snapshot = app.invoke(initial_state)
    
    # langgraph.invoke typically returns a dict of the final state
    print("\n--- Final State (JSON) ---")
    if isinstance(final_state_snapshot, dict):
        print(json.dumps(final_state_snapshot, indent=2))
    else:
        print(final_state_snapshot.model_dump_json(indent=2))

if __name__ == "__main__":
    main()
