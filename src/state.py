from typing import Annotated, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
import operator

class Evidence(BaseModel):
    """Forensic evidence gathered by Detective agents."""
    goal: str = Field(description="The specific goal or check being performed")
    found: bool = Field(description="Whether the artifact exists")
    content: Optional[str] = Field(default=None, description="The content or snippet of the evidence")
    location: str = Field(description="File path or commit hash where evidence was found")
    rationale: str = Field(description="Your rationale for your confidence on the evidence you find for this particular goal")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0 and 1")

class JudicialOpinion(BaseModel):
    """Opinion rendered by a Judge persona for a specific criterion."""
    criterion_id: str = Field(description="ID of the criterion being evaluated")
    judge: Literal["Prosecutor", "Defense", "TechLead"]

    score: int = Field(ge=1, le=5, description="Score assigned by the judge")
    argument: str = Field(description="The reasoning behind the score")
    cited_evidence: List[str] = Field(default_factory=list, description="List of evidence locations or IDs cited")

class CriterionResult(BaseModel):
    """Result of judicial synthesis for a single criterion."""
    dimension_id: str
    dimension_name: str
    final_score: int = Field(ge=1, le=5)
    judge_opinions: List[JudicialOpinion]
    dissent_summary: Optional[str] = Field(default=None, description="Required when score variance > 2")
    remediation: str = Field(description="Specific file-level instructions for improvement")

class AuditReport(BaseModel):
    """The final synthesized report from the Chief Justice."""
    repo_url: str
    executive_summary: str
    overall_score: float
    criteria: List[CriterionResult]
    remediation_plan: str

from typing_extensions import TypedDict

class AgentState(TypedDict):
    """The central state for the Automaton Auditor LangGraph."""
    repo_url: str
    pdf_path: str
    rubric_dimensions: List[Dict]
    
    # Use Annotated with reducers to aggregate evidence and opinions from parallel agents
    evidences: Annotated[Dict[str, List[Evidence]], operator.ior]
    opinions: Annotated[List[JudicialOpinion], operator.add]
    
    final_report: Optional[AuditReport]
