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

from typing_extensions import TypedDict

class AgentState(TypedDict):
    """The central state for the Automaton Auditor LangGraph."""
    github_urls: List[str]
    pdf_path: Optional[str]
    
    # Use Annotated with reducers to aggregate evidence and opinions from parallel agents
    evidences: Annotated[Dict[str, List[Evidence]], operator.ior]
    opinions: Annotated[List[JudicialOpinion], operator.add]
    
    error: Optional[str]
