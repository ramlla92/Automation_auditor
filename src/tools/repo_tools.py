# automation-auditor/src/tools/repo_tools.py
import os
import subprocess
import tempfile
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
