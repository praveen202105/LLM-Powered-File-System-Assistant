# LLM File Assistant

Full-stack local app for testing LLM-powered file system tools against the resume samples in `sample_data/resumes`.

The product has one backend source of truth and one frontend:

```text
.
├── backend/
│   ├── api.py                    # Flask API
│   ├── fs_tools.py               # read/list/write/search tools
│   └── llm_file_assistant.py     # LLM providers and FileAssistant
├── frontend/                     # React/Vite UI
├── examples/                     # examples and unit tests
├── sample_data/resumes/          # sample resume files
├── requirements.txt              # Python dependencies
└── run_app.sh                    # local launcher
```

## Quickstart

```bash
source venv/bin/activate
pip install -r requirements.txt
export GROQ_API_KEY="your-groq-key"
python -m backend.api
```

In another terminal:

```bash
cd frontend
pnpm install
pnpm dev
```

Backend: `http://localhost:5050`

Frontend: Vite prints the local URL, usually `http://localhost:5173`

You can also start both together:

```bash
./run_app.sh
```

To change the backend port:

```bash
PORT=5000 python -m backend.api
cd frontend
VITE_API_URL="http://localhost:5000" pnpm dev
```

## API

- `GET /api/health`
- `POST /api/query`
- `POST /api/reset`
- `POST /api/tools/read`
- `POST /api/tools/list`
- `POST /api/tools/write`
- `POST /api/tools/search`

Chat uses Groq by default with `llama-3.1-8b-instant` and reads `GROQ_API_KEY` from the backend environment only. Direct tools work without an LLM key.

## Examples

```bash
curl http://localhost:5050/api/health

curl -X POST http://localhost:5050/api/tools/list \
  -H "Content-Type: application/json" \
  -d '{"directory":"sample_data/resumes","extension":".txt"}'

curl -X POST http://localhost:5050/api/tools/search \
  -H "Content-Type: application/json" \
  -d '{"filepath":"sample_data/resumes/resume_john_doe.txt","keyword":"Python"}'
```

Python usage:

```python
from backend.fs_tools import list_files, read_file, search_in_file
from backend.llm_file_assistant import FileAssistant, GroqProvider

files = list_files("sample_data/resumes", ".txt")
result = search_in_file("sample_data/resumes/resume_john_doe.txt", "Python")

assistant = FileAssistant(GroqProvider(model="llama-3.1-8b-instant"))
response = assistant.run("Find resumes mentioning Python in sample_data/resumes")
```

## Verification

```bash
venv/bin/python -m py_compile backend/fs_tools.py backend/llm_file_assistant.py backend/api.py
venv/bin/python -m pytest examples/test_tools.py -q
cd frontend && pnpm build
```
