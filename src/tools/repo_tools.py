# automation-auditor/src/tools/repo_tools.py
import os
import subprocess
import tempfile
import ast
from pathlib import Path
from typing import List, Dict, Optional

class RepoCloneError(Exception):
    """Raised when repository cloning fails."""
    pass

class GitHistoryError(Exception):
    """Raised when extracting git history fails."""
    pass

def clone_repo(github_url: str) -> str:
    """
    Clones a GitHub repository into a temporary sandbox directory.
    
    Returns:
        The absolute path to the cloned repository root.
    """
    try:
        # Create a unique temporary directory
        temp_dir = tempfile.mkdtemp(prefix="auditor_sandbox_")
        
        # Extract repo name for final path construction
        repo_name = github_url.rstrip("/").split("/")[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
            
        dest_dir = os.path.join(temp_dir, repo_name)
        
        # Execute sandboxed git clone
        subprocess.run(
            ["git", "clone", github_url, dest_dir],
            capture_output=True,
            text=True,
            check=True
        )
        
        return os.path.abspath(dest_dir)
        
    except subprocess.CalledProcessError as e:
        raise RepoCloneError(f"Failed to clone repository {github_url}: {e.stderr}")
    except Exception as e:
        raise RepoCloneError(f"Unexpected error during clone: {str(e)}")

def extract_git_history(repo_path: str) -> List[Dict[str, str]]:
    """
    Extracts the git commit history in a simple format.
    
    Returns:
        A list of dictionaries containing commit hashes and messages.
    """
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--reverse"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        
        history = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            # Each line is expected to be "hash message"
            parts = line.split(" ", 1)
            if len(parts) == 2:
                history.append({"hash": parts[0], "message": parts[1]})
            else:
                history.append({"hash": parts[0], "message": ""})
                
        return history
        
    except subprocess.CalledProcessError as e:
        raise GitHistoryError(f"Failed to extract git history from {repo_path}: {e.stderr}")

def check_sidecar_files(repo_path: str) -> Dict[str, Dict]:
    """
    Checks for the existence of specific orchestration sidecar files.
    """
    path_root = Path(repo_path)
    
    check_targets = {
        "active_intents": [".orchestration/activeintents.yaml", "activeintents.yaml"],
        "agent_trace": [".orchestration/agenttrace.jsonl", "agenttrace.jsonl"]
    }
    
    results = {}
    for key, patterns in check_targets.items():
        found_data = {"exists": False, "path": None}
        for pattern in patterns:
            file_path = path_root / pattern
            if file_path.exists():
                found_data = {"exists": True, "path": str(file_path.relative_to(path_root))}
                break
        results[key] = found_data
        
    return results

def analyze_code_structure(repo_path: str) -> Dict[str, bool]:
    """
    Performs a broad check for a standard LangGraph project structure.
    """
    path_root = Path(repo_path)
    
    return {
        "graph_py": (path_root / "src/graph.py").is_file(),
        "state_py": (path_root / "src/state.py").is_file(),
        "nodes_dir": (path_root / "src/nodes").is_dir(),
        "tools_dir": (path_root / "src/tools").is_dir()
    }

def ast_analyze_source(file_path: str) -> Dict[str, any]:
    """
    Uses AST to inspect Python code for state structure and graph patterns.
    """
    if not os.path.exists(file_path):
        return {"error": "File not found"}
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
            
        findings = {
            "has_typed_dict": False,
            "has_pydantic_model": False,
            "has_parallel_edges": False
        }
        
        edges = {}
        for node in ast.walk(tree):
            # Check for inheritance (TypedDict or BaseModel)
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        if base.id == "TypedDict":
                            findings["has_typed_dict"] = True
                        if base.id == "BaseModel":
                            findings["has_pydantic_model"] = True
                    elif isinstance(base, ast.Attribute):
                        if base.attr == "TypedDict":
                            findings["has_typed_dict"] = True
                        if base.attr == "BaseModel":
                            findings["has_pydantic_model"] = True
                            
            # Check for parallel fan-out patterns
            if isinstance(node, ast.Call):
                if hasattr(node.func, "attr") and node.func.attr == "add_edge":
                    if len(node.args) >= 2:
                        arg1, arg2 = node.args[0], node.args[1]
                        if isinstance(arg1, ast.Constant) and isinstance(arg2, ast.Constant):
                            if isinstance(arg1.value, str) and isinstance(arg2.value, str):
                                from_node = arg1.value
                                to_node = arg2.value
                                if from_node not in edges:
                                    edges[from_node] = set()
                                edges[from_node].add(to_node)
                                
        for from_node, to_nodes in edges.items():
            if len(to_nodes) > 1:
                findings["has_parallel_edges"] = True
                break
                
        return findings
    except Exception as e:
        return {"error": str(e)}

def classify_git_narrative(history: List[Dict[str, str]]) -> Dict[str, any]:
    """
    Analyzes commit history to classify the development narrative.
    """
    if not history:
        return {"classification": "unknown", "reason": "No history provided", "commit_count": 0, "has_meaningful_messages": False}
        
    commit_count = len(history)
    messages = [h["message"].lower() for h in history]
    meaningful_count = len([m for m in messages if len(m) > 10])
    has_meaningful_messages = meaningful_count > (commit_count / 2)
    
    classification = "monolithic"
    if commit_count > 2:
        meaningful_prefixes = ["feat", "fix", "refactor", "docs", "chore"]
        prefix_matches = 0
        for msg in messages:
            for prefix in meaningful_prefixes:
                if msg.startswith(prefix):
                    prefix_matches += 1
                    break
                    
        # If at least 2 messages use standard prefixes, consider it atomic
        if prefix_matches >= 2:
            classification = "atomic"
            
    return {
        "commit_count": commit_count,
        "classification": classification,
        "has_meaningful_messages": has_meaningful_messages
    }

def analyze_graph_structure(path: str) -> Dict[str, bool]:
    """
    High-level AST check for StateGraph usage and parallel fan-out.
    """
    info = ast_analyze_source(path)
    return {
        "parsed_ok": "error" not in info,
        "has_typed_state": info.get("has_typed_dict", False) or info.get("has_pydantic_model", False),
        "has_parallel_edges": info.get("has_parallel_edges", False),
    }

def analyze_tool_security(repo_path: str) -> Dict[str, bool]:
    """
    Scans src/tools/ for usage of tempfile and subprocess, and lack of os.system.
    """
    tools_dir = os.path.join(repo_path, "src", "tools")
    if not os.path.exists(tools_dir):
        return {"has_tempfile": False, "has_subprocess": False, "has_os_system": False}
        
    findings = {"has_tempfile": False, "has_subprocess": False, "has_os_system": False}
    
    for root, _, files in os.walk(tools_dir):
        for file in files:
            if file.endswith(".py"):
                with open(os.path.join(root, file), "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if "tempfile" in content or "TemporaryDirectory" in content or "mkdtemp" in content:
                        findings["has_tempfile"] = True
                    if "subprocess.run" in content or "subprocess.Popen" in content:
                        findings["has_subprocess"] = True
                    if "os.system" in content:
                        findings["has_os_system"] = True
                        
    return findings

def analyze_structured_output(repo_path: str) -> Dict[str, bool]:
    """
    Scans src/nodes/judges.py for structured output enforcement and retry logic.
    """
    judges_file = os.path.join(repo_path, "src", "nodes", "judges.py")
    if not os.path.exists(judges_file):
        return {"has_structured_output": False, "has_retry_logic": False}
        
    findings = {"has_structured_output": False, "has_retry_logic": False}
    with open(judges_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        if ".with_structured_output" in content or ".bind_tools" in content:
            findings["has_structured_output"] = True
        # Look for try/except blocks associated with loops indicating retries
        if "try" in content and "except" in content and ("retry" in content.lower() or "for attempt in" in content):
            findings["has_retry_logic"] = True
            
    return findings
