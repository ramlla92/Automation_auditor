# Interim Report: Automaton Auditor - Digital Courtroom
**Date:** 2026-02-25
**Phase:** 1 & 2 (Forensic Foundation)

## Executive Summary
The foundation for the Digital Courtroom has been established. We have successfully implemented a parallel-ready forensic layer that can ingest code repositories and PDF project reports to collect evidence for future judicial review.

## Architecture Decisions So Far

### 1. State Management: TypedDict & Reducers
- **Rationale**: Transitioned from a pure Pydantic `AgentState` to a `TypedDict` with `operator` reducers. This offers better alignment with LangGraph's functional state model and ensures high-performance serialization.
- **State Schema**:
    - `github_urls`: List of targets.
    - `pdf_path`: Source report.
    - `evidences`: `Annotated[Dict, operator.ior]` - Keyed by criterion ID, allowing multiple detectors to contribute to the same forensic record without conflicts.
    - `opinions`: `Annotated[List, operator.add]` - Aggregate list for dialectical synthesis.
- **Reducers**: The use of `operator.ior` (dict union) and `operator.add` (list appends) enables seamless "Fan-in" synchronization as we scale to parallel agents.

### 2. Forensic Tooling Design
- **Sandboxed Repo Analysis**: `repo_tools.py` uses `tempfile.mkdtemp` and `subprocess.run(["git", "clone", ...], check=True)` to clone untrusted repositories into isolated directories, then:
  - runs `git log --oneline --reverse` to reconstruct the commit narrative,
  - checks orchestration sidecars (`activeintents.yaml`, `agenttrace.jsonl`),
  - and verifies the presence of core LangGraph files (`src/graph.py`, `src/state.py`, `src/nodes`, `src/tools`).
- **RAG-lite Document Analysis**: `doc_tools.py` uses `pypdf` to extract text and a simple keyword-frequency search over chunks to detect concepts such as “Cognitive Debt”, “Trust Debt”, “Dialectical Synthesis”, and “Metacognition” in the PDF report.

## Technical Accomplishments & Graph Orchestration

### 1. Detective Swarm
The current system orchestrates two primary detectives that generate structured `Evidence` objects (tracking found/not-found status, content snippets, locations, and confidence scores).

### 2. Current StateGraph Flow
The graph currently executes a sequential path that is architecturally prepared for parallel branching:
`start` -> `repo_investigator` -> `doc_analyst` -> `evidence_aggregator` -> `END`

- **`evidence_aggregator`**: Acts as the logical fan-in point where all forensic data is synchronized before being passed to the future judicial layer.

## Known Gaps and Judicial Plan

### Current Gaps
- **Judicial Layer**: Prosecutor, Defense, and Tech Lead nodes are defined as requirements but not yet implemented. The `JudicialOpinion` model is currently unused.
- **Supreme Court Engine**: The `ChiefJustice` node—responsible for applying high-level synthesis rules (Security Override, Fact Supremacy, Dissent Requirement)—is reaching implementation phase.
- **Parallelization**: Nodes currently run sequentially for deterministic verification; the "Fan-out" refactor to multiple parallel branches is scheduled for the next phase.

### Concrete Roadmap
1. **Implement Judicial Nodes**: Create agents that consume `evidences` and emit `JudicialOpinion` objects into the global state via list reducers.
2. **Synthesize Verdicts**: Build the `ChiefJustice` node to evaluate the "Dialectical Bench" (Judges), applying the rubric’s `securityoverride`, `factsupremacy`, and `dissentrequirement` rules so that confirmed security flaws cap scores, evidence outranks opinion, and disagreements between Prosecutor and Defense are explicitly summarized in the final report.
3. **Automated Reporting**: Implement a Markdown/PDF generator that synthesizes the final state into a formal audit report including Executive Summary, Criterion Breakdown, and Remediation Plans.
4. **Graph Parallelization**: Refactor the `StateGraph` wiring to utilize parallel branches for detectives and judges, maximizing throughput in large-scale audit scenarios.
