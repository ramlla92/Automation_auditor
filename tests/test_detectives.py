import pytest
from unittest.mock import patch, MagicMock
from src.state import AgentState, Evidence
from src.nodes.detectives import repo_investigator_node, doc_analyst_node

@patch("src.nodes.detectives.clone_repo")
@patch("src.nodes.detectives.extract_git_history")
@patch("src.nodes.detectives.check_sidecar_files")
@patch("src.nodes.detectives.analyze_code_structure")
def test_repo_investigator_node_success(mock_struct, mock_side, mock_hist, mock_clone):
    """Test successful repo investigation node run."""
    # Setup mocks
    mock_clone.return_value = "/tmp/repo"
    mock_hist.return_value = [{"hash": "123", "message": "init"}]
    mock_side.return_value = {"active_intents": {"exists": True, "path": "p"}}
    mock_struct.return_value = {"graph_py": True, "state_py": True, "nodes_dir": True, "tools_dir": True}
    
    state: AgentState = {
        "github_urls": ["https://github.com/user/repo"],
        "evidences": {},
        "opinions": [],
        "pdf_path": None,
        "error": None
    }
    
    result = repo_investigator_node(state)
    
    assert "git_history" in result["evidences"]
    assert result["evidences"]["git_history"][0].found is True
    assert "sidecar_files" in result["evidences"]
    assert result["evidences"]["sidecar_files"][0].found is True
    assert result.get("error") is None

@patch("src.nodes.detectives.ingest_pdf")
@patch("src.nodes.detectives.simple_keyword_search")
@patch("os.path.exists")
def test_doc_analyst_node_success(mock_exists, mock_search, mock_ingest):
    """Test successful document analysis node run."""
    mock_exists.return_value = True
    mock_ingest.return_value = ["chunk1", "chunk2"]
    mock_search.side_effect = lambda chunks, query, top_k: [f"found {query}"] if "Debt" in query else []
    
    state: AgentState = {
        "github_urls": [], 
        "pdf_path": "test.pdf",
        "evidences": {},
        "opinions": [],
        "error": None
    }
    
    result = doc_analyst_node(state)
    
    assert "theoretical_depth" in result["evidences"]
    assert result["evidences"]["theoretical_depth"][0].found is True
    assert "Cognitive Debt" in result["evidences"]["theoretical_depth"][0].content
    assert result.get("error") is None

def test_repo_investigator_no_urls():
    """Test error handling when no URLs are provided."""
    state: AgentState = {
        "github_urls": [],
        "evidences": {},
        "opinions": [],
        "pdf_path": None,
        "error": None
    }
    result = repo_investigator_node(state)
    assert result["error"] == "No GitHub URLs provided for investigation."
