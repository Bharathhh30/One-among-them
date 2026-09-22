# You are 1 among them

A playful TypeSafe / Jev experiment: describe your current state, then watch the matching characters pull themselves out of the dump.

## Run locally

### Frontend

```powershell
npm install
npm run dev
```

Open <http://localhost:5173>.

### FastAPI backend

In a second terminal:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn backend.main:app --reload --port 8000
```

The app works without credentials using a lightweight local fallback classifier. To use Jev, set `TYPESAFE_API_KEY` in the already-created `.env` file, then start the server:

```powershell
$env:TYPESAFE_API_KEY = "your_key"
uvicorn backend.main:app --reload --port 8000
```

The API key is kept in the root `.env` file and off the client. The FastAPI server calls `jev-latest` through the TypeSafe System One HTTP API. The Vite dev server proxies `/api` requests to FastAPI.
