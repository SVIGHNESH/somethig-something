# Product Requirements Document (PRD): CoFounders

## 1. Executive Summary
**CoFounders** is a multi-agent AI workforce orchestration system designed to automate the handoff between software planning and execution. By ingesting a Product Requirements Document (PRD) and a team's resumes, the system autonomously decomposes the PRD into discrete software tasks, maps them to employee skill sets using NLP, and executes the tasks by spawning dedicated AI subagents (powered by CrewAI) acting on behalf of the employees.

## 2. Problem Statement
The software delivery lifecycle often breaks down during the planning-to-execution handoff. Product managers write PRDs, which technical leads then manually read, interpret, decompose into tasks, and assign to team members. This manual process is time-consuming, prone to human error, and often results in suboptimal task assignments due to imperfect knowledge of each team member's granular skill sets. There is a need for a system that can autonomously parse requirements, understand workforce capabilities dynamically, and automate task assignment and preliminary execution.

## 3. Target Audience
*   **Product Managers / Product Owners:** To see their PRDs instantly translated into actionable technical tasks.
*   **Engineering Managers / Technical Leads:** To automate task decomposition, skill-based assignment, and identify skill gaps in the current team.
*   **Software Engineers:** To receive clearly defined tasks with context, and potentially benefit from AI-generated boilerplate or execution drafts.

## 4. Goals and Non-Goals
### 4.1. Goals
*   **Automated PRD Parsing:** Accurately extract actionable, atomic software tasks from unstructured text or PDF PRDs.
*   **Zero-Config Skill Extraction:** Parse free-text resumes (PDFs) to extract employee skills without requiring manual tagging or structured input.
*   **Intelligent Task Assignment:** Map required task skills to employee skills and assign tasks using a best-fit algorithm.
*   **Skill Gap Identification:** Surface alerts when a task requires skills not possessed by any current team member, dynamically creating a "new hire" persona.
*   **Autonomous Execution:** Spawn isolated AI agents (CrewAI) mapped to individual employees to draft code and execute tasks based on the assignments.

### 4.2. Non-Goals
*   **Replacement of Human Engineers:** The system drafts code and executes preliminary tasks; it is not intended to deploy unreviewed code to production.
*   **Global Optimal Assignment:** The hackathon implementation uses greedy best-fit assignment; it does not solve for the mathematically perfect global allocation of resources (e.g., minimizing overall project duration).
*   **Persistent State Management (V1):** The initial version is stateless per session; it does not feature a persistent database for long-term project tracking (e.g., Jira integration is out of scope for V1).

## 5. User Stories
1.  **As a Product Manager,** I want to upload a PRD (PDF or text) so that the system can automatically break it down into technical tasks without manual intervention.
2.  **As an Engineering Manager,** I want to upload my team's resumes (PDFs) so that the system understands their actual skills without me having to fill out forms.
3.  **As an Engineering Manager,** I want to see a visual board of assigned tasks so that I know who is working on what based on their strengths.
4.  **As an Engineering Manager,** I want the system to alert me if a task requires skills we don't have, so that I can initiate hiring or training.
5.  **As a Developer,** I want the system to generate the foundational CrewAI agent configurations (agents.yaml, tasks.yaml) and Python scripts, so that I don't have to write the boilerplate.
6.  **As a User,** I want to click "Run Crew" and see streaming execution logs, so I can monitor the AI agents as they build my product.

## 6. Functional Requirements

### 6.1. Frontend UI (Vanilla JS + HTML/CSS)
*   **FR-1.1 PRD Upload:** Drag-and-drop zone for `.txt` and `.pdf` files, or a text area for direct paste.
*   **FR-1.2 Resume Upload:** Drag-and-drop zone for multiple `.pdf` resume files.
*   **FR-1.3 Task Board:** Visual display of parsed tasks.
*   **FR-1.4 Employee Roster:** Visual cards displaying extracted employee information (Name, Skills, Experience, Avatar).
*   **FR-1.5 Assignment Board:** Kanban-style board mapping tasks to employees.
*   **FR-1.6 Execution Console:** Real-time terminal UI to display SSE (Server-Sent Events) logs from CrewAI execution.

### 6.2. Backend API (FastAPI)
*   **FR-2.1 `/parse-prd`:** Accepts multipart form data (file or text). Integrates with an LLM-based `task-master` to output structured JSON containing tasks, priorities, and inferred skill requirements.
*   **FR-2.2 `/parse-resume`:** Proxies to a dedicated resume parsing microservice. Extracts structured JSON (Name, Email, Phone, Skills array, Experience).
*   **FR-2.3 `/crew-generate`:** Takes parsed tasks and parsed resumes. Uses an LLM to generate `agents.yaml`, `tasks.yaml`, `crew.py`, and `main.py`. Handles gap logic (creates new synthetic agents if required skills are missing).
*   **FR-2.4 `/crew-run-stream`:** Executes the generated CrewAI project in an isolated Docker container. Streams stdout/stderr back to the client via SSE.
*   **FR-2.5 `/crew-download`:** Packages the output directory into a `.zip` file for user download.

### 6.3. AI / Logic Components
*   **FR-3.1 PRD Parser Prompting:** Must consistently output valid JSON defining tasks with `id`, `title`, `description`, `dependencies`, and `required_skills`.
*   **FR-3.2 Resume Extraction (OCR + LLM):** Must utilize Tesseract OCR/Poppler for robust text extraction from complex PDFs, followed by LLM extraction to a rigid JSON schema.
*   **FR-3.3 Matcher Algorithm:** A greedy algorithm that scores a task's `required_skills` against an employee's `skills` array. Threshold logic to determine if a "new hire" is needed.

## 7. Non-Functional Requirements
*   **NFR-1 Performance:** PRD parsing should complete within 30 seconds. Resume parsing should process at least 1 page per 5 seconds.
*   **NFR-2 Usability:** The UI must be responsive, intuitive, and provide clear loading states (spinners, toasts) during long-running LLM calls.
*   **NFR-3 Architecture Constraints:** The backend must utilize asynchronous Python (FastAPI/`asyncio`) to handle concurrent LLM requests and process streaming without blocking.
*   **NFR-4 Execution Isolation:** CrewAI subagents must run inside a Docker container to prevent generated code from executing directly on the host machine.

## 8. Data Models
### 8.1 Task Object (from PRD)
```json
{
  "id": "T1",
  "title": "Setup Database",
  "description": "Initialize PostgreSQL database with user schemas.",
  "required_skills": ["SQL", "PostgreSQL", "Database Design"],
  "priority": "High",
  "dependencies": []
}
```

### 8.2 Resume/Employee Object
```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "skills": ["Python", "SQL", "PostgreSQL", "FastAPI"],
  "total_experience_in_months": 48,
  "is_fresher": false
}
```

## 9. Future Enhancements (Post-Hackathon)
1.  **State Persistence:** Integrate a PostgreSQL database to save projects, allowing users to return to previous sessions.
2.  **Jira/Linear Integration:** Push assigned tasks directly to external issue trackers.
3.  **Global Optimization Matching:** Implement bipartite matching (e.g., Hungarian algorithm) instead of greedy assignment to optimize workload distribution.
4.  **Human-in-the-Loop:** Allow Engineering Managers to manually override LLM-suggested task assignments before Crew execution begins.
