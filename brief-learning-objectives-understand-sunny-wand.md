# Resume File Assistant — LLM Tool Calling Assignment

## Context
Assignment: build LLM tool-calling system over local file system for resume files. Two deliverables: `fs_tools.py` (file ops) + `llm_file_assistant.py` (LLM wired to tools). Must run zero-cost — use **Ollama** (local model, no API key, no billing) instead of paid Anthropic/OpenAI. Project built phase by phase, not all at once, so each stage can be tested before moving on.

Project root: `c:\Nabil\Projects\LLM-Powered-File-System-Assistant` (existing repo).

## Current folder structure (actual, as scaffolded)
```
LLM-Powered-File-System-Assistant/
├── ai/
│   └── llm_file_assistant.py   (empty, Phase 4 target)
├── backend/
│   ├── __init__.py
│   └── fs_tools.py             (empty, Phase 2 target)
├── resumes/                    (empty, Phase 3 sample data)
├── output/                     (empty, generated summaries)
├── venv/                       (already created)
├── requirements.txt            (empty)
└── README.md                   (empty)
```
Note: deviates from original flat layout — `fs_tools.py` lives in `backend/`, `llm_file_assistant.py` lives in `ai/`. Plan updated to match.

## Prerequisites (user action, not code)
- Install Ollama (https://ollama.com), then `ollama pull llama3.1` (supports native tool/function calling).
- Python 3.10+, venv — already created at `venv/`.

## Phase 0 — Environment check (do first)
- Confirm `venv/` activates: `venv\Scripts\Activate.ps1` (PowerShell) or `venv/Scripts/activate` (bash).
- Confirm Ollama installed + reachable: `ollama --version`, `ollama list`.
- Pull model: `ollama pull llama3.1`.
- Confirm Python version inside venv: `python --version` (need 3.10+).
- Verify: venv activates clean, `ollama list` shows daemon running, model pulled.

## Phase 1 — Scaffold
- Folders already exist (`ai/`, `backend/`, `resumes/`, `output/`, `venv/`) — nothing to create.
- Fill `requirements.txt`: `ollama`, `pypdf`, `python-docx`.
- `fs_tools.py`, `llm_file_assistant.py`, `README.md` already present but empty — no action needed, just confirmed in place.
- Verify: `pip install -r requirements.txt` succeeds inside venv.

## Phase 2 — `backend/fs_tools.py` (Part A, core logic, no LLM yet)
Four functions, each returns dict/list (never raises — catch and return `{"success": False, "error": ...}`):
- `read_file(filepath)`: dispatch by extension — `.txt` plain read, `.pdf` via `pypdf.PdfReader`, `.docx` via `python-docx`. Return `{"success", "content", "metadata": {"filename", "extension", "size_bytes", "num_chars"}}`.
- `list_files(directory, extension=None)`: `os.listdir` + `os.stat`, filter by extension if given, return list of `{"name", "size_bytes", "modified"}`.
- `write_file(filepath, content)`: `os.makedirs(..., exist_ok=True)` on parent dir, write, return `{"success", "filepath"}`.
- `search_in_file(filepath, keyword)`: read via `read_file`, case-insensitive substring search line by line, return `{"success", "matches": [{"line_number", "context"}]}`.

Verify: standalone `if __name__ == "__main__"` smoke test block, run manually against `resumes/`.

## Phase 3 — Sample data
Generate 6-8 short dummy `.txt` resumes in `resumes/` (varied names, some mentioning "Python", some not — needed for the search demo query). Keep synthetic/generic, no real people.

## Phase 4 — `ai/llm_file_assistant.py` (Part B, tool calling)
- Use `ollama` Python SDK — `ollama.chat(model="llama3.1", messages=..., tools=[...])`. It supports OpenAI-style tool schemas natively.
- Import `fs_tools` functions from `backend.fs_tools` (need `ai/` and `backend/` both importable — run from project root, or add root to `sys.path`).
- Define JSON tool schemas for the 4 `fs_tools` functions (name, description, parameters).
- Agent loop: send user query + tool schemas → if response has `tool_calls`, dispatch to matching `fs_tools` function by name, feed result back as a `tool` role message → repeat until model returns plain text.
- CLI entrypoint: `python ai/llm_file_assistant.py "Find resumes mentioning Python experience"` (argv or simple input loop, run from project root).
- Support the 3 example queries from the brief as manual test cases.

Verify: run all 3 example queries, confirm correct tool(s) invoked and sane final answer.

## Phase 5 — Docs
- `README.md`: setup (Ollama install + pull, venv, pip install), how to run, example commands/output.
- `requirements.txt` finalized.

## Phase 6 — Demo video
Not code — user records 2-3 min screen capture running the 3 example queries after Phase 4 works. Flag as manual step, not something to automate.

## Notes
- Build/test phases sequentially — do not write Phase 4 before Phase 2/3 are verified working.
- No API keys, no cost: everything runs against local Ollama daemon.
