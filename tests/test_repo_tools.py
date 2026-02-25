import pytest
import os
import shutil
import tempfile
from pathlib import Path
from src.tools.repo_tools import (
    clone_repo, 
    extract_git_history, 
    check_sidecar_files, 
    analyze_code_structure,
    RepoCloneError,
    GitHistoryError
)

def test_analyze_code_structure_fake_repo():
    """Test structure analysis with a mock directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        src_path = Path(temp_dir) / "src"
        src_path.mkdir()
        (src_path / "graph.py").touch()
        (src_path / "state.py").touch()
        (src_path / "nodes").mkdir()
        (src_path / "tools").mkdir()
        
        results = analyze_code_structure(temp_dir)
        assert results["graph_py"] is True
        assert results["state_py"] is True
        assert results["nodes_dir"] is True
        assert results["tools_dir"] is True

def test_check_sidecar_files_fake_repo():
    """Test sidecar file detection with a mock directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        orch_path = Path(temp_dir) / ".orchestration"
        orch_path.mkdir()
        (orch_path / "activeintents.yaml").touch()
        
        results = check_sidecar_files(temp_dir)
        assert results["active_intents"]["exists"] is True
        assert results["active_intents"]["path"] == os.path.join(".orchestration", "activeintents.yaml")
        assert results["agent_trace"]["exists"] is False

def test_clone_repo_invalid_url():
    """Test that invalid URLs raise RepoCloneError."""
    with pytest.raises(RepoCloneError):
        clone_repo("https://github.com/nonexistent/repo_that_does_not_exist_12345")

# Note: Integration tests for clone_repo and extract_git_history 
# would require a real internet connection and git installed.
# We'll stick to logic/unit tests for now.
