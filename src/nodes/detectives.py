# automation-auditor/src/nodes/detectives.py
import os
from ..state import AgentState, Evidence
from ..tools.repo_tools import (
    clone_repo, 
    extract_git_history, 
    check_sidecar_files, 
    analyze_code_structure, 
    RepoCloneError, 
    GitHistoryError
)
from ..tools.doc_tools import ingest_pdf, simple_keyword_search

def _append_evidence(state: AgentState, criterion_id: str, evidence: Evidence) -> AgentState:
    """
    Helper to safely append evidence to the state.
    """
    if criterion_id not in state.get("evidences", {}):
        state.setdefault("evidences", {})[criterion_id] = []
    state["evidences"][criterion_id].append(evidence)
    return state

def repo_investigator_node(state: AgentState) -> AgentState:
    """
    Node that clones the repository and performs code forensics.
    """
    github_urls = state.get("github_urls", [])
    if not github_urls:
        state["error"] = "No GitHub URLs provided for investigation."
        return state
    
    # Process the first URL for now
    url = github_urls[0]
    
    try:
        # 1. Clone
        repo_path = clone_repo(url)
        
        # 2. Extract Git History
        history = extract_git_history(repo_path)
        _append_evidence(state, "git_history", Evidence(
            found=True,
            content=f"Extracted {len(history)} commits from history.",
            location="git:log",
            confidence=1.0
        ))
        
        # 3. Sidecar Check
        sidecars = check_sidecar_files(repo_path)
        active_intents = sidecars.get("active_intents", {})
        agent_trace = sidecars.get("agent_trace", {})
        
        summary = []
        if active_intents.get("exists"):
            summary.append(f"ActiveIntents found at {active_intents['path']}")
        if agent_trace.get("exists"):
            summary.append(f"AgentTrace found at {agent_trace['path']}")
            
        _append_evidence(state, "sidecar_files", Evidence(
            found=bool(summary),
            content=" | ".join(summary) if summary else "No orchestration sidecars detected.",
            location=".orchestration/",
            confidence=0.9
        ))
        
        # 4. Structure Analysis
        structure = analyze_code_structure(repo_path)
        missing = [k for k, v in structure.items() if not v]
        
        _append_evidence(state, "repo_structure", Evidence(
            found=len(missing) == 0,
            content=f"Structure valid. Missing: {missing}" if missing else "Full folder structure verified.",
            location="src/",
            confidence=0.8
        ))
        
    except (RepoCloneError, GitHistoryError) as e:
        state["error"] = str(e)
        _append_evidence(state, "git_history", Evidence(
            found=False,
            content=f"Forensic collection failed: {str(e)}",
            location="repo_root",
            confidence=0.0
        ))
        
    return state

def doc_analyst_node(state: AgentState) -> AgentState:
    """
    Node that parses the PDF report and checks for theoretical depth.
    """
    pdf_path = state.get("pdf_path")
    if not pdf_path:
        state["error"] = "No PDF path provided for analysis."
        return state
        
    if not os.path.exists(pdf_path):
        state["error"] = f"PDF file not found: {pdf_path}"
        return state
        
    try:
        # 1. Ingest
        chunks = ingest_pdf(pdf_path)
        
        # 2. Search for theoretical concepts
        queries = ["Cognitive Debt", "Trust Debt", "Dialectical Synthesis", "Metacognition"]
        findings = []
        
        for query in queries:
            matches = simple_keyword_search(chunks, query, top_k=1)
            if matches:
                findings.append(f"Match for '{query}': {matches[0][:100]}...")
        
        _append_evidence(state, "theoretical_depth", Evidence(
            found=len(findings) > 0,
            content="\n".join(findings) if findings else "No advanced theoretical concepts detected in report.",
            location="pdf:theoretical_depth",
            confidence=0.8
        ))
        
    except Exception as e:
        state["error"] = f"PDF analysis failed: {str(e)}"
        
    return state
