from typing import Annotated, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator
import operator

class Evidence(BaseModel):
    """Forensic evidence gathered by Detective agents."""
    found: bool = Field(description="Whether the artifact exists")
    content: Optional[str] = Field(default=None, description="The content or snippet of the evidence")
    location: Optional[str] = Field(default=None, description="File path or commit hash where evidence was found")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0 and 1")

class JudicialOpinion(BaseModel):
    """Opinion rendered by a Judge persona for a specific criterion."""
    judge: Literal["Prosecutor", "Defense", "TechLead"]
    score: int = Field(ge=1, le=5, description="Score assigned by the judge")
    argument: str = Field(description="The reasoning behind the score")
    cited_evidence: List[str] = Field(default_factory=list, description="List of evidence locations or IDs cited")

class AgentState(BaseModel):
    """The central state for the Automaton Auditor LangGraph."""
    github_urls: List[str] = Field(default_factory=list, description="The list of GitHub repository URLs to audit")
    pdf_path: Optional[str] = Field(default=None, description="Path to the PDF report to audit")
    
    # Use reducers to aggregate evidence and opinions from parallel agents
    evidences: Dict[str, List[Evidence]] = Field(
        default_factory=dict, 
        description="Evidence collected, keyed by criterion ID"
    )
    opinions: Dict[str, List[JudicialOpinion]] = Field(
        default_factory=dict, 
        description="Judicial opinions, keyed by criterion ID"
    )
    
    error: Optional[str] = Field(default=None, description="Any error encountered during the audit")

    # In LangGraph, we'd typically use TypedDict for the actual state passed between nodes,
    # but the user asked for Pydantic models here. 
    # For LangGraph integration, we'll likely wrap these or use them directly.
