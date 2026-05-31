# LLM File Assistant Frontend

React/Vite UI for the root Flask backend in `backend/`.

## Local Development

From the repository root:

```bash
source venv/bin/activate
pip install -r requirements.txt
export GROQ_API_KEY="your-groq-key"
python -m backend.api
```

In a second terminal:

```bash
cd frontend
pnpm install
pnpm dev
```

The frontend uses `http://localhost:5050` by default. Override it with:

```bash
VITE_API_URL="http://localhost:5000" pnpm dev
```

## Product Shape

- Chat Interface calls `/api/query`.
- Direct Tools call `/api/tools/*`.
- File Browser lists and previews files from `sample_data/resumes`.
- API keys stay server-side in the backend environment.
