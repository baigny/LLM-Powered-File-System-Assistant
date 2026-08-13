# Resume File Assistant — LLM Tool Calling

A local, zero-cost LLM tool-calling system over resume files. An LLM (Ollama, running `llama3.1` locally — no API key, no billing) decides which file-system tool to call based on a natural-language query, then answers using the real tool results.

## Project structure

```
LLM-Powered-File-System-Assistant/
├── backend/
│   ├── __init__.py
│   └── fs_tools.py           # Part A — file system tools
├── ai/
│   └── llm_file_assistant.py # Part B — LLM + tool-calling agent
├── resumes/                  # sample resume data
├── output/                   # scratch output dir
├── requirements.txt
└── README.md
```

## Setup

### 1. Install Ollama and pull the model

Download and install Ollama from https://ollama.com, then pull the model used by this project:

```bash
ollama pull llama3.1
```

Confirm it's installed and the model is available:

```bash
ollama --version
ollama list
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Installs `ollama` (Python SDK), `pypdf` (PDF reading), and `python-docx` (DOCX reading).

## Part A — `backend/fs_tools.py`

Four core file-system functions, each returns a dict/list and never raises (errors are caught and returned as `{"success": False, "error": ...}`):

| Function | Description |
|---|---|
| `read_file(filepath)` | Reads `.txt`, `.pdf`, or `.docx`. Also accepts a **directory** path — reads every file inside in one call. |
| `list_files(directory, extension=None)` | Lists files in a directory, optional extension filter. |
| `write_file(filepath, content)` | Writes content to a file, creating parent directories as needed. |
| `search_in_file(filepath, keyword)` | Case-insensitive keyword search. Also accepts a **directory** — searches every file in one call, grouped by file. |

Run the standalone smoke test:

```bash
venv\Scripts\python.exe backend\fs_tools.py
```

## Part B — `ai/llm_file_assistant.py`

Wires the 4 tools above to `llama3.1` via `ollama.chat(..., tools=[...])`. The agent loop: send the query + tool schemas, if the model requests a tool call run it and feed the result back, repeat until the model returns plain text.

Run from the project root:

```bash
venv\Scripts\python.exe ai\llm_file_assistant.py "your query here"
```

Or with no argument, it prompts for input interactively.

## Example queries

The 3 official example queries from the assignment brief:

```bash
venv\Scripts\python.exe ai\llm_file_assistant.py "Read all resumes in the resumes folder"
venv\Scripts\python.exe ai\llm_file_assistant.py "Find resumes mentioning Python experience"
venv\Scripts\python.exe ai\llm_file_assistant.py "Create a summary file for resume_john_doe.pdf"
```

1. **Read all resumes** — the model calls `read_file` once on the `resumes` directory and summarizes every file's real content.
2. **Find resumes mentioning Python experience** — `search_in_file` does a literal, case-insensitive substring match, and the phrase "python experience" doesn't appear verbatim in any sample resume (they say things like "Python and Django"), so this exact wording legitimately returns no matches. Run it with just **"Find resumes mentioning Python"** to get real matches — the model calls `search_in_file` once on the directory and reports which files actually contain "python".
3. **Create a summary file** — use a real filename from `resumes/` (e.g. `taylor_nguyen.txt`) since `resume_john_doe.pdf` doesn't exist in the sample data. The model reads the target resume and answers with a short, paraphrased 3-4 sentence summary; the CLI then saves that text to `<name>_summary.txt` next to the source file (see note below on why this step isn't left entirely to the model).

## Known limitation: local model reliability

`llama3.1:8b` running locally is noticeably less reliable at multi-step tool calling than a hosted model like GPT-4 or Claude — this is a real, observed constraint of the assignment's "zero-cost, local model" requirement, not a bug in `fs_tools.py`. Specifically, it would sometimes:

- hallucinate filenames instead of using ones from a prior `list_files` result
- invent tools that don't exist
- loop through files one at a time instead of using one call, and skip some
- for the write-a-summary step specifically: **narrate** the `write_file(...)` call as plain text in its answer instead of emitting a real tool call, meaning no file was actually written, with no error raised

Mitigations applied (see `ai/llm_file_assistant.py`):

- The system prompt forces one-shot **directory-mode** calls for "read all" / "search all" queries, instead of letting the model loop per-file — this is the fix for hallucinated filenames and skipped files.
- The "create a summary" flow no longer asks the model to call `write_file` at all. The model just answers with the summary text (the same reliable path used for query 1), and the Python CLI code writes that text to disk itself. This sidesteps the narrated-tool-call failure instead of trying to parse it out of free text.

## requirements.txt

```
ollama
pypdf
python-docx
```
