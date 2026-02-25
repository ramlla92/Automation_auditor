# Automaton Auditor – Digital Courtroom

## Setup and Environment
This project uses `uv` for dependency management.

1. **Install Dependencies**:
   ```bash
   uv sync
   ```

2. **Configure Environment**:
   Copy `.env.example` to `.env` and fill in your API keys (LangSmith, OpenAI/Gemini).
   ```bash
   cp .env.example .env
   ```

3. **Run Demo Graph**:
   Execute the smoke test graph to verify LangGraph and LangSmith integration.
   ```bash
   uv run python run_graph.py
   ```

## Getting Started (Detailed)

### Prerequisites
- **Python**: Version 3.11 or higher.
- **uv**: The "extremely fast Python package installer and resolver". [Install uv](https://docs.astral.sh/uv/getting-started/installation/).

### Setup
1. **Sync Dependencies**:
   Install all project dependencies into a local virtual environment.
   ```bash
   uv sync
   ```
2. **Environment Configuration**:
   Create your local environment file from the template.
   ```bash
   cp .env.example .env
   ```
   *Edit `.env` and provide your `LANGCHAIN_API_KEY` and `OPENAI_API_KEY` (or `GOOGLE_API_KEY`).*

### Running the Detective Graph
The current system runs a forensic pipeline consisting of the `RepoInvestigator` and `DocAnalyst`.
To invoke the graph with default test inputs, run:
```bash
uv run python run_graph.py
```
This script initializes the `AgentState` with a repository URL and a PDF path, then executes the LangGraph `StateGraph`. Findings are printed to the console and traced in LangSmith.
