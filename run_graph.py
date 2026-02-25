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
    
    # 3. Create initial state (dictionary for TypedDict)
    initial_state: AgentState = {
        "github_urls": ["https://github.com/example/repo"],
        "pdf_path": "report.pdf",
        "evidences": {},
        "opinions": [],
        "error": None
    }
    
    # 4. Invoke the app
    print("--- Invoking LangGraph ---")
    final_state_snapshot = app.invoke(initial_state)
    
    # langgraph.invoke returns the state snapshot
    print("\n--- Final State ---")
    print(final_state_snapshot)

if __name__ == "__main__":
    main()
