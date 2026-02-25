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
   uv run python automation-auditor/run_graph.py
   ```
