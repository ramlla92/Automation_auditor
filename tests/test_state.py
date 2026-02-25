import pytest
from pydantic import ValidationError
from src.state import Evidence, JudicialOpinion, AgentState


def test_evidence_valid():
    """Test valid evidence instantiation."""
    ev = Evidence(
        found=True,
        content="found state.py",
        location="src/state.py",
        confidence=0.9,
    )
    assert ev.found is True
    assert ev.confidence == 0.9


def test_evidence_invalid_confidence():
    """Test that confidence must be between 0 and 1."""
    with pytest.raises(ValidationError):
        Evidence(found=True, confidence=1.5)
    with pytest.raises(ValidationError):
        Evidence(found=True, confidence=-0.1)


def test_judicial_opinion_valid():
    """Test valid judicial opinion."""
    opinion = JudicialOpinion(
        judge="Prosecutor",
        score=2,
        argument="Missing Pydantic models",
        cited_evidence=["src/graph.py"],
    )
    assert opinion.judge == "Prosecutor"
    assert opinion.score == 2


def test_judicial_opinion_invalid_score():
    """Test that score must be between 1 and 5."""
    with pytest.raises(ValidationError):
        JudicialOpinion(judge="Defense", score=6, argument="too good")
    with pytest.raises(ValidationError):
        JudicialOpinion(judge="TechLead", score=0, argument="too bad")


def test_agent_state_initial_state():
    """Test initial AgentState."""
    state = AgentState(
        github_urls=["https://github.com/user/repo"],
        pdf_path=None,
    )
    assert state.github_urls == ["https://github.com/user/repo"]
    assert state.evidences == {}
    assert state.opinions == {}
    assert state.error is None
