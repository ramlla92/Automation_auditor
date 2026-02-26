# automation-auditor/src/nodes/detectives.py
import os
from ..state import AgentState, Evidence
from ..tools.repo_tools import (
    clone_repo, 
    extract_git_history, 
    check_sidecar_files, 
    analyze_code_structure, 
    ast_analyze_source,
    classify_git_narrative,
    analyze_graph_structure,
    RepoCloneError, 
    GitHistoryError
)
from ..tools.doc_tools import ingest_pdf, verify_citations, analyze_concept_depth
from ..tools.vision_tools import extract_images_from_pdf

def _append_evidence(new_evidences: dict, criterion_id: str, evidence: Evidence):
    """
    Helper to safely append evidence to the updates dict.
    """
    if criterion_id not in new_evidences:
        new_evidences[criterion_id] = []
    new_evidences[criterion_id].append(evidence)

def repo_investigator_node(state: AgentState) -> AgentState:
    """
    Node that clones the repository and performs code forensics.
    """
    repo_url = state.get("repo_url")
    if not repo_url:
        print("Error: No repo_url provided for investigation.")
        return state
    
    url = repo_url
    
    new_evidences = {}
    
    try:
        # 1. Clone
        repo_path = clone_repo(url)
        
        # 2. Extract Git History (Maps to dimension: git_forensic_analysis)
        history = extract_git_history(repo_path)
        _append_evidence(new_evidences, "git_history", Evidence(
            goal="Extract Git History for progression analysis",
            found=True,
            content=f"Extracted {len(history)} commits from history.",
            location="git:log",
            rationale="Collected git log --oneline --reverse to show development progression.",
            confidence=1.0
        ))
        
        # 3. Sidecar Check (Ad-hoc / Not strictly rubric but good intel)
        sidecars = check_sidecar_files(repo_path)
        active_intents = sidecars.get("active_intents", {})
        agent_trace = sidecars.get("agent_trace", {})
        
        summary = []
        if active_intents.get("exists"):
            summary.append(f"ActiveIntents found at {active_intents['path']}")
        if agent_trace.get("exists"):
            summary.append(f"AgentTrace found at {agent_trace['path']}")
            
        _append_evidence(new_evidences, "sidecar_files", Evidence(
            goal="Identify orchestration sidecar files",
            found=bool(summary),
            content=" | ".join(summary) if summary else "No orchestration sidecars detected.",
            location=".orchestration/",
            rationale="Checked specific predefined paths for ActiveIntents and AgentTrace files.",
            confidence=0.9
        ))
        
        # 4. Structure Analysis (Maps to dimension: safe_tool_engineering / layout)
        structure = analyze_code_structure(repo_path)
        missing = [k for k, v in structure.items() if not v]
        
        _append_evidence(new_evidences, "repo_structure", Evidence(
            goal="Verify root structure of the LangGraph project",
            found=len(missing) == 0,
            content=f"Structure valid. Missing: {missing}" if missing else "Full folder structure verified.",
            location="src/",
            rationale="Checked for standard src/graph.py, src/state.py, nodes/ and tools/ directories.",
            confidence=0.8
        ))

        # 5. Advanced Repo Checks: Protocol A (Maps to dimension: state_management_rigor)
        state_file = os.path.join(repo_path, "src", "state.py")
        state_info = ast_analyze_source(state_file)
        if "error" in state_info:
            _append_evidence(new_evidences, "state_structure", Evidence(
                goal="Parse state.py for error",
                found=False,
                content=f"Error analyzing state.py: {state_info['error']}",
                location="src/state.py",
                rationale="AST parsing failed on state file.",
                confidence=1.0
            ))
        else:
            found_types = state_info.get("has_typed_dict", False) or state_info.get("has_pydantic_model", False)
            _append_evidence(new_evidences, "state_structure", Evidence(
                goal="AST check for Pydantic/TypedDict state models",
                found=found_types,
                content=f"State types detected: TypedDict={state_info.get('has_typed_dict')}, BaseModel={state_info.get('has_pydantic_model')}",
                location="src/state.py",
                rationale="Used AST parsing to confidently detect inheritance from TypedDict or BaseModel.",
                confidence=1.0
            ))
        
        # Protocol B: Graph Parallelism (Maps to dimension: graph_orchestration)
        graph_file = os.path.join(repo_path, "src", "graph.py")
        graph_info = analyze_graph_structure(graph_file)
        if not graph_info["parsed_ok"]:
            _append_evidence(new_evidences, "graph_parallelism", Evidence(
                goal="Parse graph.py for error",
                found=False,
                content="Error analyzing graph.py AST.",
                location="src/graph.py",
                rationale="AST parsing wrapper reported parsed_ok=False.",
                confidence=1.0
            ))
        else:
            has_fanout = graph_info.get("has_parallel_edges", False)
            content_msg = "Parallel fan-out edges detected in graph wiring." if has_fanout else "Graph appears linear; no fan-out edges found."
            _append_evidence(new_evidences, "graph_parallelism", Evidence(
                goal="Detect fan-out orchestration patterns in StateGraph",
                found=has_fanout,
                content=content_msg,
                location="src/graph.py",
                rationale="AST parsed builder.add_edge calls indicating multiple outgoing paths.",
                confidence=0.9
            ))
        
        # Protocol C: Git Narrative (Maps to dimension: git_forensic_analysis)
        narrative = classify_git_narrative(history)
        _append_evidence(new_evidences, "git_narrative", Evidence(
            goal="Analyze git history for step-by-step meaningful commits",
            found=True,
            content=f"Repository has {narrative['commit_count']} commits. Classification: {narrative['classification']}. Meaningful messages: {narrative['has_meaningful_messages']}.",
            location="git:log",
            rationale="Applied semantic checks on git messages and overall commit count.",
            confidence=0.9
        ))
        
    except (RepoCloneError, GitHistoryError) as e:
        print(f"Error RepoInvestigator: {str(e)}")
        _append_evidence(new_evidences, "git_history", Evidence(
            goal="Catch forensic collection failure",
            found=False,
            content=f"Forensic collection failed: {str(e)}",
            location="repo_root",
            rationale="Subprocess exception during clone or history extraction.",
            confidence=0.0
        ))
        
    return {"evidences": new_evidences}

def doc_analyst_node(state: AgentState) -> AgentState:
    """
    Node that parses the PDF report and checks for theoretical depth.
    """
    pdf_path = state.get("pdf_path")
    if not pdf_path:
        print("Error: No PDF path provided for analysis.")
        return state
        
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        return state
        
    new_evidences = {}
    try:
        # 1. Ingest
        chunks = ingest_pdf(pdf_path)
        raw_text = "".join(chunks)
        
        # 2. Search for theoretical concepts: Protocol B (Maps to dimension: theoretical_depth)
        queries = ["Dialectical Synthesis", "Metacognition", "Fan-In", "Fan-Out", "State Synchronization"]
        findings = []
        
        for query in queries:
            depth_info = analyze_concept_depth(raw_text, query)
            finding_text = f"{query}: {depth_info['classification']}"
            if "context_snippet" in depth_info and depth_info["context_snippet"]:
                finding_text += f" - \"{depth_info['context_snippet'][:100]}...\""
            findings.append(finding_text)
        
        _append_evidence(new_evidences, "theoretical_depth", Evidence(
            goal="Evaluate integration of buzzwords with substantive explanations",
            found=True,
            content="\n".join(findings),
            location="pdf:theoretical_depth",
            rationale="Used heuristic text analysis for depth indicators around concept keywords.",
            confidence=0.8
        ))

        # 3. Citation Integrity Check: Protocol A (Maps to dimension: report_accuracy)
        known_files = state.get("known_files", ["src/graph.py", "src/state.py", "src/nodes/detectives.py"])
        citations = verify_citations(raw_text, known_files)
        
        hallucinated = [c for c in citations if c["classification"] == "hallucinated"]
        if hallucinated:
            hall_summary = [f"{c['path']} (in claim: '{c['claim_sentence'][:60]}...') " for c in hallucinated]
            content_val = "Citations verified with hallucinations detected: " + ", ".join(hall_summary)
        else:
            content_val = "All cited files verified in repository."
            
        _append_evidence(new_evidences, "citation_integrity", Evidence(
            goal="Verify all file paths mentioned in PDF exist in repo",
            found=len(hallucinated) == 0,
            content=content_val,
            location="pdf:citations",
            rationale="Regex path extraction followed by direct existence check vs known_files.",
            confidence=0.9
        ))
        
    except Exception as e:
        print(f"PDF analysis failed: {str(e)}")
        
    return {"evidences": new_evidences}

def vision_inspector_node(state: AgentState) -> AgentState:
    """
    Parallel stub for visual flow analysis. 
    In the future, this will use Docling/Vision models to analyze diagrams.
    """
    print("--- Running VisionInspector (Stub) ---")
    
    new_evidences = {}
    pdf_path = state.get("pdf_path")
    if pdf_path and os.path.exists(pdf_path):
        images = extract_images_from_pdf(pdf_path)
        img_count = len(images)
        
        expected = "Detectives (parallel) -> EvidenceAggregator -> Judges (parallel) -> ChiefJustice"
        # Maps to dimension: swarm_visual
        _append_evidence(new_evidences, "flow_analysis", Evidence(
            goal="Analyze architectural diagram structural flow",
            found=False,
            content=f"{img_count} images extracted (vision analysis stub). expected_flow: {expected}",
            location="pdf:images",
            rationale="VisionInspector is a stub for future multimodal diagram parsing. Currently extracts images but does not evaluate them via LLM.",
            confidence=0.5
        ))
    else:
        # Maps to dimension: swarm_visual
        _append_evidence(new_evidences, "flow_analysis", Evidence(
            goal="Analyze architectural diagram structural flow",
            found=False,
            content="VisionInspector stub: Visual flow analysis not yet implemented. No PDF provided.",
            location="pdf:images",
            rationale="VisionInspector is a stub for future multimodal diagram parsing.",
            confidence=0.5
        ))
    
    return {"evidences": new_evidences}
