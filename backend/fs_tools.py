import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None


def read_file(filepath: str) -> Dict[str, Any]:
    """
    Read and extract text from resume files (PDF, TXT, DOCX).

    Args:
        filepath: Path to the file to read

    Returns:
        Dictionary with success status, content, metadata, and error info
    """
    try:
        path = Path(filepath)

        if not path.exists():
            return {
                "success": False,
                "filepath": filepath,
                "content": "",
                "metadata": {},
                "error": f"File not found: {filepath}"
            }

        if not path.is_file():
            return {
                "success": False,
                "filepath": filepath,
                "content": "",
                "metadata": {},
                "error": f"Path is not a file: {filepath}"
            }

        file_type = path.suffix.lower()
        stat = path.stat()
        modified_date = datetime.fromtimestamp(stat.st_mtime).isoformat()

        if file_type == ".txt":
            content = _read_txt(path)
        elif file_type == ".pdf":
            content = _read_pdf(path)
        elif file_type == ".docx":
            content = _read_docx(path)
        else:
            return {
                "success": False,
                "filepath": filepath,
                "content": "",
                "metadata": {},
                "error": f"Unsupported file type: {file_type}"
            }

        word_count = len(content.split())

        return {
            "success": True,
            "filepath": str(path),
            "content": content,
            "metadata": {
                "size_bytes": stat.st_size,
                "modified_date": modified_date,
                "word_count": word_count,
                "file_type": file_type
            },
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "filepath": filepath,
            "content": "",
            "metadata": {},
            "error": f"Error reading file: {str(e)}"
        }


def _read_txt(path: Path) -> str:
    """Read plain text file with encoding detection."""
    encodings = ["utf-8", "latin-1", "cp1252"]

    for encoding in encodings:
        try:
            return path.read_text(encoding=encoding)
        except (UnicodeDecodeError, LookupError):
            continue

    return path.read_text(encoding="utf-8", errors="ignore")


def _read_pdf(path: Path) -> str:
    """Extract text from PDF file."""
    if PdfReader is None:
        return f"[PDF parsing unavailable - PyPDF2 not installed] File: {path.name}"

    try:
        reader = PdfReader(str(path))
        text_parts = []

        for page_num, page in enumerate(reader.pages):
            try:
                text_parts.append(page.extract_text())
            except Exception as e:
                text_parts.append(f"[Error extracting page {page_num + 1}: {str(e)}]")

        return "\n".join(text_parts)
    except Exception as e:
        return f"[Error reading PDF: {str(e)}]"


def _read_docx(path: Path) -> str:
    """Extract text from DOCX file."""
    if Document is None:
        return f"[DOCX parsing unavailable - python-docx not installed] File: {path.name}"

    try:
        doc = Document(str(path))
        paragraphs = [para.text for para in doc.paragraphs]
        return "\n".join(paragraphs)
    except Exception as e:
        return f"[Error reading DOCX: {str(e)}]"


def list_files(directory: str, extension: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all files in a directory with optional extension filter.

    Args:
        directory: Directory path to list
        extension: Optional file extension filter (e.g., ".pdf", ".txt")

    Returns:
        List of file dictionaries with metadata, sorted by modified date (newest first)
    """
    try:
        dir_path = Path(directory)

        if not dir_path.exists():
            return []

        if not dir_path.is_dir():
            return []

        files = []

        for file_path in dir_path.iterdir():
            if not file_path.is_file():
                continue

            if extension and not file_path.suffix.lower() == extension.lower():
                continue

            stat = file_path.stat()
            modified_date = datetime.fromtimestamp(stat.st_mtime).isoformat()

            files.append({
                "filename": file_path.name,
                "filepath": str(file_path),
                "size_bytes": stat.st_size,
                "modified_date": modified_date,
                "file_type": file_path.suffix.lower()
            })

        files.sort(key=lambda x: x["modified_date"], reverse=True)
        return files

    except Exception:
        return []


def write_file(filepath: str, content: str) -> Dict[str, Any]:
    """
    Write content to a text file, creating directories if needed.

    Args:
        filepath: Path to write to
        content: Content to write

    Returns:
        Dictionary with success status, file info, and error info
    """
    try:
        path = Path(filepath)

        _validate_path_safety(path)

        path.parent.mkdir(parents=True, exist_ok=True)

        overwrite_warning = None
        if path.exists():
            overwrite_warning = f"Overwriting existing file: {filepath}"

        path.write_text(content, encoding="utf-8")

        stat = path.stat()

        return {
            "success": True,
            "filepath": str(path),
            "size_bytes": stat.st_size,
            "message": overwrite_warning or "File written successfully",
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "filepath": filepath,
            "size_bytes": 0,
            "message": "",
            "error": f"Error writing file: {str(e)}"
        }


def _validate_path_safety(path: Path) -> None:
    """Validate that path doesn't attempt path traversal attacks."""
    try:
        path.resolve()
    except (ValueError, RuntimeError) as e:
        raise ValueError(f"Invalid path: {str(e)}")


def search_in_file(filepath: str, keyword: str) -> Dict[str, Any]:
    """
    Search for keywords in file content.

    Args:
        filepath: Path to file to search
        keyword: Keyword to find (case-insensitive)

    Returns:
        Dictionary with search results and context
    """
    try:
        file_result = read_file(filepath)

        if not file_result["success"]:
            return {
                "success": False,
                "filepath": filepath,
                "keyword": keyword,
                "match_count": 0,
                "matches": [],
                "error": file_result["error"]
            }

        content = file_result["content"]
        lines = content.split("\n")
        keyword_lower = keyword.lower()

        matches = []

        if not keyword:
            return {
                "success": True,
                "filepath": filepath,
                "keyword": keyword,
                "match_count": 0,
                "matches": matches,
                "error": None
            }

        for line_num, line in enumerate(lines, start=1):
            line_lower = line.lower()
            search_start = 0

            while True:
                column = line_lower.find(keyword_lower, search_start)
                if column == -1:
                    break

                context_before = lines[max(0, line_num - 3):line_num - 1]
                context_after = lines[line_num:min(len(lines), line_num + 2)]

                matches.append({
                    "line_number": line_num,
                    "column": column + 1,
                    "match_text": line.strip(),
                    "context_before": context_before,
                    "context_after": context_after
                })
                search_start = column + len(keyword_lower)

        return {
            "success": True,
            "filepath": filepath,
            "keyword": keyword,
            "match_count": len(matches),
            "matches": matches,
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "filepath": filepath,
            "keyword": keyword,
            "match_count": 0,
            "matches": [],
            "error": f"Error searching file: {str(e)}"
        }
