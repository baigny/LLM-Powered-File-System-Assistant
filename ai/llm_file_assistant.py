import sys
import os
import json
import textwrap
import ollama

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend import fs_tools

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file (.txt, .pdf, .docx) and return its content. Pass a directory path (e.g. 'resumes') to read every file in it at once, or a single file path to read just that one.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to a file OR a directory to read"},
                },
                "required": ["filepath"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in a directory, optionally filtered by file extension.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory to list files from"},
                    "extension": {"type": "string", "description": "Optional extension filter, e.g. '.txt'"},
                },
                "required": ["directory"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write text content to a file, creating parent directories if needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to write the file to"},
                    "content": {"type": "string", "description": "Text content to write"},
                },
                "required": ["filepath", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_in_file",
            "description": "Search for a keyword, case-insensitive. Pass a single file path to search just that file, or a directory path (e.g. 'resumes') to search every file in it at once.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to a file OR a directory to search"},
                    "keyword": {"type": "string", "description": "A single simple keyword, e.g. 'python'"},
                },
                "required": ["filepath", "keyword"],
            },
        },
    },
]

def dispatch_tool(name, args):
    try:
        if name == "read_file":
            return fs_tools.read_file(args["filepath"])
        elif name == "list_files":
            return fs_tools.list_files(args["directory"], args.get("extension"))
        elif name == "write_file":
            return fs_tools.write_file(args["filepath"], args["content"])
        elif name == "search_in_file":
            return fs_tools.search_in_file(args["filepath"], args["keyword"])
        else:
            return {"success": False, "error": f"Unknown tool: {name}"}
    except KeyError as e:
        return {"success": False, "error": f"Missing required argument: {e}"}

def run_agent(query, model="llama3.1"):
    messages = [
        {
            "role": "system",
            "content": (
                "You are a file assistant. You only have 4 tools: read_file, list_files, "
                "write_file, search_in_file. Never invent other tools, filenames, or commands.\n\n"
                "Resumes are in the 'resumes' directory. Always call list_files first to get "
                "real filenames, then use the EXACT name it returns (e.g. if list_files returns "
                "'alex_morgan.txt', call search_in_file with filepath 'resumes/alex_morgan.txt' "
                "— never invent a name like 'file1.txt').\n\n"
                "To find files by topic, call search_in_file ONCE with the directory path itself "
                "(e.g. search_in_file('resumes', 'python')) — it searches every file in one call "
                "and returns matches grouped by file. Do not call list_files first for this, and "
                "do not call search_in_file per-file. Use one simple keyword (e.g. 'python'), not "
                "a full phrase. Report every file the result actually contains — never skip one, "
                "never claim 'no others match' without checking the full result.\n\n"
                "If asked to READ ALL files in a folder, call read_file ONCE with the "
                "directory path itself (e.g. read_file('resumes')) — it returns every file's "
                "content in one call. Include the real content from the result in your answer. "
                "Never fabricate resume content — only report what the tool actually returned.\n\n"
                "If asked to CREATE A SUMMARY, call read_file to get the real content, then "
                "answer with a CONCISE summary in your own words — 3-4 sentences, one short "
                "paragraph, no bullet points, no section headers. Do not copy sentences or bullet "
                "points verbatim from the source — paraphrase and condense. Cover only the "
                "person's role, years of experience, and top 3-4 skills; leave out minor details. "
                "Do NOT call write_file yourself, do not mention write_file at all. Saving the "
                "file is handled separately after you answer."
            ),

        },
        {"role": "user", "content": query},
    ]

    last_read_filepath = None

    while True:
        response = ollama.chat(model=model, messages=messages, tools=TOOLS)
        msg = response["message"]
        messages.append(msg)

        tool_calls = msg.get("tool_calls")
        if not tool_calls:
            return msg.get("content", ""), last_read_filepath

        for call in tool_calls:
            name = call["function"]["name"]
            args = call["function"]["arguments"]
            print(f"[TOOL CALL] {name}({args})")
            result = dispatch_tool(name, args)
            print(f"[TOOL RESULT] {result}")
            if name == "read_file" and "filepath" in args and not os.path.isdir(args["filepath"]):
                last_read_filepath = args["filepath"]
            messages.append({
                "role": "tool",
                "content": json.dumps(result),
            })

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter your query: ")

    answer, source_filepath = run_agent(query)
    print(answer)

    if "summary" in query.lower() and source_filepath:
        base = os.path.splitext(os.path.basename(source_filepath))[0]
        output_path = os.path.join(os.path.dirname(source_filepath), f"{base}_summary.txt")
        wrapped_answer = "\n".join(
            textwrap.fill(paragraph, width=80) for paragraph in answer.splitlines()
        )
        result = fs_tools.write_file(output_path, wrapped_answer)
        if result["success"]:
            print(f"\n[SAVED] Summary written to {output_path}")
        else:
            print(f"\n[ERROR] Could not save summary: {result['error']}")
