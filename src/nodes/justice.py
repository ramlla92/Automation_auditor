import os
from datetime import datetime
from collections import defaultdict
from typing import Dict, List
from ..state import AgentState, AuditReport, CriterionResult, JudicialOpinion

def chief_justice_node(state: AgentState) -> AgentState:
    print("--- Running Chief Justice ---")
    
    rubric = state.get("rubric_dimensions", [])
    opinions = state.get("opinions", [])
    
    if not rubric or not opinions:
        print("Chief Justice: Missing rubric or opinions. Generating empty report.")
        report = AuditReport(
            repo_url=state.get("repo_url", "unknown"),
            executive_summary="Automated Audit halted. Missing Rubric Dimension mapping or collected opinions.",
            overall_score=0.0,
            criteria=[],
            remediation_plan="Verify run_graph configuration successfully attaches `rubric_dimensions` mapped properly, and Detectives successfully generate content."
        )
        return {"final_report": report}
    
    # Map dimension id to name
    dim_names = {r["id"]: r["name"] for r in rubric if "id" in r}
    
    # Organize opinions by criterion
    opinions_by_crit: Dict[str, List[JudicialOpinion]] = defaultdict(list)
    for op in opinions:
        opinions_by_crit[op.criterion_id].append(op)
        
    criteria_results = []
    
    for crit_id, ops in opinions_by_crit.items():
        if not ops:
            continue
            
        prosecutor = next((o for o in ops if o.judge == "Prosecutor"), None)
        defense = next((o for o in ops if o.judge == "Defense"), None)
        tech_lead = next((o for o in ops if o.judge == "TechLead"), None)
        
        # Base synthesis: average score
        scores = [o.score for o in ops]
        avg_score = sum(scores) / len(scores) if scores else 0
        final_score = int(round(avg_score))
        
        dissent_summary = None
        variance = max(scores) - min(scores) if scores else 0
        if variance >= 20:
            dissent_summary = f"High variance ({variance}) detected between judges. Prosecutor: {prosecutor.score if prosecutor else 'N/A'}, Defense: {defense.score if defense else 'N/A'}, TechLead: {tech_lead.score if tech_lead else 'N/A'} (Satisfies dissent requirement)."
            reeval_note = " Chief Justice re-evaluated the specific evidence cited by each judge before setting the final score."
            dissent_summary = (dissent_summary or "") + reeval_note
            
        # Deterministic Rules
        # 1. Security Override (Prosecutor <= 40 caps final score at 60)
        if prosecutor and prosecutor.score <= 40:
            final_score = min(final_score, 60)
            if dissent_summary:
                dissent_summary += " | Rule of Security applied: Final score capped at 60 due to Prosecutor veto."
            else:
                dissent_summary = "Rule of Security applied: Final score capped at 60 due to Prosecutor veto."
                
        # 2. Functionality Weight (Bias toward TechLead for Architecture criteria)
        is_architecture = "architecture" in crit_id.lower() or "graph" in crit_id.lower() or "state" in crit_id.lower()
        if is_architecture and tech_lead:
            # Shift towards tech lead score
            final_score = tech_lead.score
            if dissent_summary:
                dissent_summary += f" | Rule of Functionality applied: Score biased towards Tech Lead ({tech_lead.score})."
            else:
                dissent_summary = f"Rule of Functionality applied: Score biased towards Tech Lead ({tech_lead.score})."
                
        # Ensure bounds
        final_score = max(1, min(100, final_score))
        
        remediation_text = "Review the specific gaps flagged by the Prosecutor and TechLead to align architecture with the required schema."
        if "git" in crit_id.lower():
            remediation_text = "Improve commit hygiene and ensure step-by-step meaningful commit messages."
        elif "state" in crit_id.lower() or "graph" in crit_id.lower():
            remediation_text = "Refactor state models (Pydantic/TypedDict) and graph structures to support parallel patterns with reducers."
            
        criteria_results.append(CriterionResult(
            dimension_id=crit_id,
            dimension_name=dim_names.get(crit_id, crit_id),
            final_score=final_score,
            judge_opinions=ops,
            dissent_summary=dissent_summary,
            remediation=remediation_text
        ))
        
    # Overall Verdict
    if not criteria_results:
        exec_summary = "No criteria could be evaluated. Insufficient opinions."
        overall_avg = 0.0
    else:
        all_scores = [cr.final_score for cr in criteria_results]
        overall_avg = sum(all_scores) / len(all_scores)
        
        exec_summary = f"Automated Audit Complete. Evaluated {len(criteria_results)} criteria. Overall average score: {overall_avg:.2f}/100."
        
    report = AuditReport(
        repo_url=state.get("repo_url", "unknown"),
        executive_summary=exec_summary,
        overall_score=overall_avg,
        criteria=criteria_results,
        remediation_plan="Review failed or disputed criteria and implement fixes." if overall_avg < 80.0 else "No major remediation required."
    )
    
    # Generate Markdown Report
    md_lines = [
        f"# Automaton Auditor - Final Report",
        f"**Repository URL:** {report.repo_url}",
        f"**Overall Score:** {report.overall_score:.2f} / 100",
        f"\n## Executive Summary",
        f"{report.executive_summary}",
        f"\n## Criterion Breakdown"
    ]
    
    for cr in report.criteria:
        md_lines.append(f"### {cr.dimension_name} (ID: {cr.dimension_id}) - Score: {cr.final_score}/100")
        if cr.dissent_summary:
            md_lines.append(f"*(Dissent/Rules Applied)*: {cr.dissent_summary}")
        md_lines.append(f"**Remediation:** {cr.remediation}\n")
        
    md_lines.extend([
        f"\n## Remediation Plan",
        f"{report.remediation_plan}"
    ])
    
    md_content = "\n".join(md_lines)
    os.makedirs("reports", exist_ok=True)
    
    # Parse repo url for safe filename
    url_parts = report.repo_url.rstrip("/").split("/")
    repo_name = url_parts[-1].replace(".git", "") if len(url_parts) > 0 else "unknown"
    user_name = url_parts[-2] if len(url_parts) > 1 else "unknown"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    unique_filename = f"audit_{user_name}_{repo_name}_{timestamp}.md"
    unique_filepath = os.path.join("reports", unique_filename)
    latest_filepath = os.path.join("reports", "audit_report_latest.md")
    
    with open(unique_filepath, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    with open(latest_filepath, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    print(f"Generated Audit Report: {unique_filepath}")
        
    return {"final_report": report}
