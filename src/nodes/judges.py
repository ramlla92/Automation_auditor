import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from ..state import AgentState, JudicialOpinion, Evidence

def get_llm():
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)
    
class OpinionsResponse(BaseModel):
    opinions: List[JudicialOpinion]

def judge_node(state: AgentState, persona: str, perspective_prompt: str) -> AgentState:
    llm = get_llm()
    llm_with_tools = llm.with_structured_output(OpinionsResponse)
    
    rubric = state.get("rubric_dimensions", [])
    if not rubric:
        print(f"{persona} Node: Skipping judgment because rubric_dimensions is empty.")
        return {}
        
    evidences = state.get("evidences", {})
    
    system_msg = f"""You are the {persona} Judge in an automated audit courtroom.

Your perspective:
{perspective_prompt}

You are given:
1) Rubric dimensions (each with an "id" and "name"):
{json.dumps(rubric, indent=2)}

2) Forensic evidence collected by detectives:
{json.dumps(evidences, default=str, indent=2)}

Your task:
- For EVERY dimension in the rubric list, create EXACTLY ONE JudicialOpinion.
- Set `criterion_id` to that dimension's "id" (do not invent new IDs).
- Set `judge` to "{persona}" exactly.
- Score each dimension from 1–100, based ONLY on the rubric and evidence. Evidence outweighs opinion.
- Use `cited_evidence` to list any file paths, IDs, or snippets you reference.

Failure handling:
- If rubric or evidence are missing, empty, or clearly insufficient:
  - Assume an upstream failure in the Detectives layer.
  - STILL return one JudicialOpinion per dimension using this safe default:
    - score: 1
    - argument: "Unable to evaluate this criterion due to missing or empty evidence. Upstream detectives failed to provide contents, triggering a safe default."
    - cited_evidence: []

Hard rules:
- NEVER return an empty message, blank string, null, or [] for any field.
- NEVER return an empty opinions list.
- NEVER say "no comment".
- When in doubt, fall back to the safe default opinion instead of leaving anything empty.

Output:
Return a JSON object matching the OpinionsResponse schema:
{{
  "opinions": [
    {{
      "judge": "...",
      "criterion_id": "...",
      "score": ...,
      "argument": "...",
      "cited_evidence": ["...", "..."]
    }}
  ]
}}
"""
    
    user_msg = (
        "Generate one JudicialOpinion per rubric dimension, following all rules above. "
        "If evidence is missing or empty, use the safe fallback opinion instead of leaving any field blank."
    )
    messages = [
        ("system", system_msg),
        ("human", user_msg),
    ]
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = llm_with_tools.invoke(messages)
            if response and response.opinions:
                # Ensure opinions list exists in state updates
                return {"opinions": response.opinions}
            
            # If parsed successfully but returned empty list
            error_msg = "You returned an empty opinions list. You MUST return exactly ONE JudicialOpinion for each dimension ID."
            print(f"{persona} Node Warning: Empty opinions returned on attempt {attempt+1}")
            messages.append(("human", error_msg))
            
        except Exception as e:
            print(f"Error in {persona} node (attempt {attempt+1}): {e}")
            if attempt == max_retries - 1:
                return {}
            # Pass validation error back to the LLM to learn and fix
            messages.append(("human", f"Your previous output failed validation: {str(e)}\nPlease correct the formatting and ensure all required fields are present."))
            
    return {}
    
def prosecutor_node(state: AgentState) -> AgentState:
    print("--- Running Prosecutor Judge ---")
    prompt = "You actively look for flaws, security risks, missing requirements, and negative theoretical debt. Your goal is to critically audit and penalize shortcomings."
    return judge_node(state, "Prosecutor", prompt)

def defense_node(state: AgentState) -> AgentState:
    print("--- Running Defense Judge ---")
    prompt = "You highlight the strengths, functional completeness, positive architectural decisions, and mitigating factors. Defend the implementation's merits."
    return judge_node(state, "Defense", prompt)

def techlead_node(state: AgentState) -> AgentState:
    print("--- Running TechLead Judge ---")
    prompt = "You are a pragmatic Tech Lead. You weigh the Prosecutor's strictness against the Defense's leniency. Focus on realistic maintainability, architecture, and practical tradeoffs."
    return judge_node(state, "TechLead", prompt)
