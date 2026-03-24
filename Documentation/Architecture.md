# System Architecture: CoFounders

This document outlines the high-level architecture of the CoFounders multi-agent orchestration system.

## 1. High-Level Architecture Diagram

```text
    User Interface (Vanilla JS/React)
          │
          │ (REST / SSE)
          ▼
    ┌────────────────────────────────────────┐
    │           Main API (FastAPI)           │
    │               Port: 8000               │
    └────┬────────────────────────────┬──────┘
         │                            │
  (PRD & Crew Logic)           (Resume Proxy)
         │                            │
         ▼                            ▼
┌──────────────────┐       ┌──────────────────────┐
│  PRD Parser      │       │ Resume Parser API    │
│  (task-master)   │       │ (FastAPI, Port 8001) │
└──────────────────┘       └────┬────────────┬────┘
                                │            │
                           (Tesseract)    (Poppler)
                                ▼
                       ┌─────────────────────────┐
                       │  Gemini 2.0 / OpenAI    │
                       └─────────────────────────┘
         │
    (Crew Generation)
         ▼
┌──────────────────────────────────────────────┐
│             CrewAI Orchestrator              │
│  - agents.yaml, tasks.yaml, crew.py          │
└──────────────────────┬───────────────────────┘
                       │
             (Docker Execution)
                       ▼
    ┌────────────────────────────────────────┐
    │     Isolated Docker Container          │
    │     (Subagent Execution Environment)   │
    └────────────────────────────────────────┘
```

## 2. Component Details

### 2.1 Frontend (ourplan-frontend)

* **Tech Stack:** HTML5, CSS3, Vanilla JavaScript.
* **Responsibility:** Handles file uploads (drag-and-drop), manages application state across the multi-step wizard, renders data visualizations (task boards, resume cards), and handles SSE streams for real-time console logging.

### 2.2 Main Backend API (ourplan-backend)

* **Tech Stack:** Python 3.12+, FastAPI, Uvicorn, UV package manager.
* **Responsibility:** The central orchestration hub.
  * Exposes endpoints to the frontend.
  * Invokes the PRD parsing logic.
  * Proxies resume files to the specialized parsing service.
  * Executes the assignment algorithm.
  * Generates the CrewAI codebase (Python + YAML).
  * Spawns Docker containers to run the generated Crew.

### 2.3 Resume Parser Microservice (Port 8001)

* **Tech Stack:** Python, FastAPI, Tesseract OCR, Poppler, LLM SDKs.
* **Responsibility:** A dedicated service for extracting text from heavily formatted PDF resumes. It uses OCR to guarantee text extraction regardless of PDF construction, then passes the raw text to an LLM to extract a strict JSON schema.

### 2.4 Agent Execution Engine (CrewAI)

* **Tech Stack:** CrewAI framework, Docker.
* **Responsibility:** Transforms the logical mapping of employees to tasks into runnable software agents. Each employee is represented as an Agent with specific tools and goals; each task is represented as a Task. The engine executes these sequentially or hierarchically as defined by the generation step. Docker is used to sandbox the environment preventing code injection risks on the host machine.

## 3. Data Flow

1. **Ingestion:** User uploads PRD and Resumes via UI.
2. **Decomposition:** Main API sends PRD to `task-master`, returning a JSON array of technical tasks.
3. **Extraction:** Main API sends Resumes to the Resume Parser Microservice. The microservice returns structured JSON profiles for each employee.
4. **Matching & Generation:** The Main API feeds tasks and employee profiles to an LLM (Gemini 2.0). The LLM acts as the "Matcher," deciding who does what and writing the CrewAI configuration files (`agents.yaml`, `tasks.yaml`, `crew.py`) to disk.
5. **Execution:** The user clicks "Run". The backend builds a Docker image containing the newly generated CrewAI code and executes it, streaming the output logs back to the user interface via Server-Sent Events (SSE).
