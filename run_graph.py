# automation-auditor/run_graph.py
import json
import os
from src.graph import build_graph
from src.state import AgentState
from src.config import init_tracing

def main():
    # 1. Initialize Tracing
    init_tracing()
    
    # 2. Build the Graph
    app = build_graph()
    
    # 3. Create initial state (dictionary for TypedDict)
    rubric_payload = []
    rubric_path = "rubric/week2_rubric.json"
    if os.path.exists(rubric_path):
        with open(rubric_path, "r", encoding="utf-8") as f:
            rubric_payload = json.load(f).get("dimensions", [])
            
    initial_state: AgentState = {
        "repo_url": "https://github.com/example/repo",
        "pdf_path": "report.pdf",
        "rubric_dimensions": rubric_payload,
        "evidences": {},
        "opinions": [],
        "final_report": None
    }
    
    # 4. Invoke the app
    print("--- Invoking LangGraph ---")
    final_state_snapshot = app.invoke(initial_state)
    
    # langgraph.invoke returns the state snapshot
    print("\n--- Final State ---")
    
    final_report = final_state_snapshot.get("final_report")
    if final_report:
        print(f"\nFinal Overall Score: {final_report.overall_score:.2f} / 5.0")
        print(f"MD Report Output: c:\\Users\\THINKPAD\\Desktop\\10_Academy_AI\\Week_2\\automation-auditor\\reports\\audit_report.md")
    else:
        print("Graph finished, but no Final Report was generated.")

if __name__ == "__main__":
    main()
