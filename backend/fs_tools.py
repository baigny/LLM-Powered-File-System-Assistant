import os
from pypdf import PdfReader
from docx import Document

def read_file(filepath):
    try:
        ext = os.path.splitext(filepath)[1].lower()

        if ext == ".txt":
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        elif ext == ".pdf":
            reader = PdfReader(filepath)
            content = "\n".join(page.extract_text() or "" for page in reader.pages)
        elif ext == ".docx":
            doc = Document(filepath)
            content = "\n".join(p.text for p in doc.paragraphs)
        else:
            return {"success": False, "error": f"Unsupported extension: {ext}"}

        stat = os.stat(filepath)
        return {
            "success": True,
            "content": content,
            "metadata": {
                "filename": os.path.basename(filepath),
                "extension": ext,
                "size_bytes": stat.st_size,
                "num_chars": len(content),
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def list_files(directory, extension=None):
    try:
        files = []
        for name in os.listdir(directory):
            path = os.path.join(directory, name)
            if not os.path.isfile(path):
                continue
            if extension and not name.lower().endswith(extension.lower()):
                continue
            stat = os.stat(path)
            files.append({
                "name": name,
                "size_bytes": stat.st_size,
                "modified": stat.st_mtime,
            })
        return files
    except Exception as e:
        return [{"success": False, "error": str(e)}]

def write_file(filepath, content):
    try:
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return {"success": True, "filepath": filepath}
    except Exception as e:
        return {"success": False, "error": str(e)}

def search_in_file(filepath, keyword):
    try:
        result = read_file(filepath)
        if not result["success"]:
            return result

        matches = []
        for i, line in enumerate(result["content"].splitlines(), start=1):
            if keyword.lower() in line.lower():
                matches.append({"line_number": i, "context": line.strip()})

        return {"success": True, "matches": matches}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    print(list_files("resumes"))
    print(write_file("output/smoke_test.txt", "hello from fs_tools smoke test"))
