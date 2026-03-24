# API Reference

This document details the REST API endpoints exposed by the CoFounders backend services.

## Main Backend API (Port 8000)
Base URL: `http://localhost:8000`

### 1. Health Check
*   **Endpoint:** `/health/`
*   **Method:** `GET`
*   **Description:** Verifies that the main orchestration service is running.
*   **Response:**
    ```json
    {
      "status": "ok"
    }
    ```

### 2. Parse PRD
*   **Endpoint:** `/parse-prd`
*   **Method:** `POST`
*   **Content-Type:** `multipart/form-data`
*   **Description:** Ingests a PRD and returns a structured list of software tasks.
*   **Parameters:**
    *   `text` (string, optional): Raw text of the PRD.
    *   `file` (file, optional): A `.txt` or `.pdf` file upload. *Note: Provide either `text` or `file`.*
*   **Response (Success - 200 OK):**
    ```json
    {
      "master": {
        "tasks": [
          {
            "id": 1,
            "title": "Database Schema Design",
            "description": "Design user and product tables.",
            "priority": "high",
            "dependencies": [],
            "status": "pending"
          }
        ]
      }
    }
    ```

### 3. Parse Resume
*   **Endpoint:** `/parse-resume`
*   **Method:** `POST`
*   **Content-Type:** `multipart/form-data`
*   **Description:** Proxies the PDF to the Resume Parser microservice and saves the extracted JSON locally.
*   **Parameters:**
    *   `file` (file, required): A PDF format resume.
*   **Response (Success - 200 OK):**
    ```json
    {
      "message": "Resume parsed and saved.",
      "saved_as": "jane_doe.json",
      "data": {
        "extracted_info": {
          "name": "Jane Doe",
          "skills": ["Python", "FastAPI"],
          "total_experience_in_months": 24
        }
      }
    }
    ```

### 4. Generate Crew Config
*   **Endpoint:** `/crew-generate`
*   **Method:** `POST`
*   **Description:** Reads the previously parsed tasks and resumes from the local file system and uses an LLM to generate CrewAI configuration files (`agents.yaml`, `tasks.yaml`, `crew.py`, `main.py`).
*   **Query Parameters:**
    *   `output_subdir` (string, default: `output`): The directory to write the generated files.
*   **Response (Success - 200 OK):**
    ```json
    {
      "written_files": {
        "agents.yaml": "/path/to/agents.yaml",
        "tasks.yaml": "/path/to/tasks.yaml"
      },
      "agents_yaml": "...",
      "tasks_yaml": "...",
      "new_agents": ["DevOps Engineer"],
      "output_dir": "/path/to/output/"
    }
    ```

### 5. Run Crew (Streaming)
*   **Endpoint:** `/crew-run-stream`
*   **Method:** `POST`
*   **Description:** Builds a Docker container from the generated configurations and executes the AI agents, streaming the standard output back to the client.
*   **Response:** `text/event-stream` (SSE Events)
    *   Format: `data: {"type": "log", "line": "Agent Jane is writing code..."}`

### 6. Download Crew Output
*   **Endpoint:** `/crew-download`
*   **Method:** `GET`
*   **Description:** Downloads the results of the CrewAI execution as a compressed zip file.
*   **Response:** `application/zip` (Binary file download)

---

## Resume Parser API (Port 8001)
Base URL: `http://localhost:8001`

### 1. Direct Parsing
*   **Endpoint:** `/api/v1/resume/parse`
*   **Method:** `POST`
*   **Content-Type:** `multipart/form-data`
*   **Description:** Directly processes a PDF using Tesseract OCR and an LLM to extract structured data.
*   **Parameters:**
    *   `file` (file, required): PDF resume.
*   **Response:** JSON object containing parsed metrics (`extracted_info`).