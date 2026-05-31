import os
from typing import Any, Dict

from flask import Flask, jsonify, request
from flask_cors import CORS

from backend.fs_tools import list_files, read_file, search_in_file, write_file
from backend.llm_file_assistant import FileAssistant, GroqProvider


DEFAULT_PROVIDER = "groq"
DEFAULT_MODEL = "llama-3.1-8b-instant"

app = Flask(__name__)
CORS(app)


def _json_body() -> Dict[str, Any]:
    return request.get_json(silent=True) or {}


def _error(message: str, status: int = 400):
    return jsonify({"success": False, "error": message}), status


def _make_assistant() -> FileAssistant:
    if not os.getenv("GROQ_API_KEY"):
        raise ValueError("GROQ_API_KEY is not configured in the backend environment.")
    return FileAssistant(GroqProvider(model=DEFAULT_MODEL))


@app.get("/api/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "provider": DEFAULT_PROVIDER,
        "model": DEFAULT_MODEL,
        "groq_api_key_set": bool(os.getenv("GROQ_API_KEY")),
    })


@app.post("/api/query")
def query_assistant():
    data = _json_body()
    query = (data.get("query") or "").strip()
    max_iterations = data.get("max_iterations", 10)

    if not query:
        return _error("Query is required.")

    try:
        max_iterations = int(max_iterations)
    except (TypeError, ValueError):
        return _error("max_iterations must be an integer.")

    try:
        assistant = _make_assistant()
        result = assistant.run_with_trace(query, max_iterations=max_iterations)
        status = 200 if result.get("success") else 500
        return jsonify(result), status
    except ValueError as e:
        return _error(str(e), 400)
    except Exception as e:
        return _error(str(e), 500)


@app.post("/api/reset")
def reset_conversation():
    return jsonify({"success": True})


@app.post("/api/tools/read")
def read_file_endpoint():
    data = _json_body()
    filepath = data.get("filepath", "")
    if not filepath:
        return _error("filepath is required.")
    return jsonify(read_file(filepath))


@app.post("/api/tools/list")
def list_files_endpoint():
    data = _json_body()
    directory = data.get("directory", "")
    extension = data.get("extension") or None
    if not directory:
        return _error("directory is required.")
    return jsonify(list_files(directory, extension))


@app.post("/api/tools/write")
def write_file_endpoint():
    data = _json_body()
    filepath = data.get("filepath", "")
    content = data.get("content", "")
    if not filepath:
        return _error("filepath is required.")
    return jsonify(write_file(filepath, content))


@app.post("/api/tools/search")
def search_file_endpoint():
    data = _json_body()
    filepath = data.get("filepath", "")
    keyword = data.get("keyword", "")
    if not filepath:
        return _error("filepath is required.")
    if not keyword:
        return _error("keyword is required.")
    return jsonify(search_in_file(filepath, keyword))


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5050"))
    app.run(host="0.0.0.0", port=port, debug=True)
