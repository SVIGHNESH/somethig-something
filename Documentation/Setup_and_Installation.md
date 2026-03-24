# Setup and Installation Guide

This guide will walk you through setting up the CoFounders project on your local machine.

## Prerequisites
Before you begin, ensure you have the following installed on your system:
*   **Python 3.12+**
*   **Node.js & npm** (Required for the `task-master` dependency and local frontend serving)
*   **Docker Desktop** (Must be running to execute the CrewAI agents in an isolated environment)
*   **uv** (The extremely fast Python package installer and resolver)
    *   Install via: `pip install uv`

## 1. Clone the Repository
```bash
git clone <repository_url>
cd Neurax-CoFounders
```

## 2. Environment Variables Setup
You need API keys for the LLMs to function properly.

1.  **Main Backend:** Create a `.env` file in `code/ourplan-backend/`.
    ```env
    CREW_MODEL=gemini-2.0-flash
    CREW_API_KEY=your_gemini_api_key_here
    ```

2.  **Resume Parser:** Create a `.env` file inside `code/ourplan-backend/resume_parser_api/` (Note: Ensure this directory exists or pull the submodule if it's external).
    ```env
    LLM_API_KEY=your_openai_or_gemini_key
    ```

## 3. Backend Setup
We use `uv` for lightning-fast dependency management.

### Main API (Port 8000)
```bash
cd code/ourplan-backend
uv sync
```

### Resume Parser API (Port 8001)
*Note: This requires Tesseract and Poppler. On Windows, the hackathon codebase assumes these are bundled in the directory. On Linux/Mac, you will need to install them globally.*
*   **Ubuntu/Debian:** `sudo apt-get install tesseract-ocr poppler-utils`
*   **MacOS:** `brew install tesseract poppler`

```bash
cd code/ourplan-backend/resume_parser_api
uv sync
```

### Fix Hardcoded Paths (Linux/Mac Users)
The hackathon codebase contains hardcoded Windows paths. Before running on Linux/Mac, you must update the following files:
*   `code/ourplan-backend/routes/parse_prd.py`: Change `TMP_DIR` to a relative path like `./tmp`.
*   `code/ourplan-backend/services/prd_parser.py`: Ensure `TASKMASTER_CMD` points to your global `npm` bin path (e.g., `task-master`) and `TASKS_JSON_PATH` is relative.

## 4. Frontend Setup
The frontend is plain HTML/JS/CSS, so it does not require a build step. However, it needs to be served via a local web server to avoid CORS issues.

```bash
cd code/ourplan-frontend
npx serve . -p 3000
```
*(Alternatively, use Python's built-in server: `python -m http.server 3000`)*

## 5. Running the Application
To run everything simultaneously, you can use the provided PowerShell script (Windows) or run the commands manually in separate terminal tabs.

**Windows:**
```powershell
cd code/ourplan-backend
.\start_servers.ps1
```

**Linux / Mac (Manual Start):**
*Terminal 1 (Main Backend):*
```bash
cd code/ourplan-backend
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

*Terminal 2 (Resume Parser):*
```bash
cd code/ourplan-backend/resume_parser_api
uv run python main.py
```

*Terminal 3 (Frontend):*
```bash
cd code/ourplan-frontend
python -m http.server 3000
```

**Access the UI:**
Open your browser and navigate to `http://localhost:3000`.