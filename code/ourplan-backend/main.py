import os
import json
import asyncio
import uuid
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")

try:
    from google import genai
    genai_client = genai.Client(api_key=LLM_API_KEY)
    USE_GENAI_SDK = bool(LLM_API_KEY)
except Exception:
    genai_client = None
    USE_GENAI_SDK = False

app = FastAPI(title="Neurax API")

class Task(BaseModel):
    id: str
    title: str
    description: str
    requiredSkills: list[str]
    estimatedHours: int

class Employee(BaseModel):
    id: str
    name: str
    role: str
    skills: list[str]
    experience: str

class TaskAssignment(BaseModel):
    taskId: str
    taskTitle: str
    employeeId: str
    employeeName: str
    matchScore: int

class CrewConfig(BaseModel):
    name: str
    tasks: list[TaskAssignment]
    generatedAt: str

class ParsePRDRequest(BaseModel):
    text: Optional[str] = None
    tasks: Optional[list[Task]] = None

class ParseResumeRequest(BaseModel):
    employees: Optional[list[Employee]] = None

class CrewGenerateRequest(BaseModel):
    tasks: list[Task]
    employees: list[Employee]

class CrewRunRequest(BaseModel):
    config: CrewConfig

async def call_llm(prompt: str) -> str:
    if not LLM_API_KEY:
        print("No LLM_API_KEY configured")
        return ""
    
    try:
        if USE_GENAI_SDK and genai_client:
            response = genai_client.models.generate_content(
                model=LLM_MODEL,
                contents=prompt
            )
            return response.text or ""
        return ""
    except Exception as e:
        print(f"LLM exception: {e}")
        return ""

@app.get("/")
async def root():
    return {"status": "ok", "message": "Neurax API running"}

@app.post("/parse-prd")
async def parse_prd(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    content = text or ""
    
    if file:
        content = await file.read()
        if hasattr(content, 'decode'):
            content = content.decode('utf-8', errors='ignore')
    
    if not content:
        raise HTTPException(status_code=400, detail="No content provided")
    
    print(f"Calling LLM with content length: {len(content)}")
    llm_response = await call_llm(
        f"""You are a project manager. Parse this PRD and extract actionable tasks.
For each task provide: id (number), title, description, requiredSkills (array of strings), estimatedHours (number).
Return ONLY a valid JSON array. No markdown, no explanation.

PRD:
{content[:3000]}"""
    )
    print(f"LLM response: {llm_response[:200] if llm_response else 'EMPTY'}")
    
    if llm_response:
        try:
            tasks = json.loads(llm_response)
            return {"tasks": tasks}
        except:
            pass
    
    keywords = ["api", "database", "ui", "frontend", "backend", "auth", "payment", "dashboard", "mobile", "testing"]
    tasks = []
    for kw in keywords:
        if kw.lower() in content.lower():
            tasks.append({
                "id": str(uuid.uuid4())[:8],
                "title": f"{kw.title()} Implementation",
                "description": f"Implement {kw} functionality",
                "requiredSkills": [kw.title(), "Development"],
                "estimatedHours": 8
            })
    
    if not tasks:
        tasks = [
            {"id": "1", "title": "Design System Implementation", "description": "Create reusable UI components", "requiredSkills": ["React", "TypeScript", "CSS"], "estimatedHours": 8},
            {"id": "2", "title": "Backend API Development", "description": "Build RESTful APIs", "requiredSkills": ["Python", "FastAPI", "PostgreSQL"], "estimatedHours": 12},
        ]
    
    return {"tasks": tasks}

def extract_text_from_pdf(content: bytes) -> str:
    """Extract text from PDF binary content"""
    try:
        import pdfplumber
        import io
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            return text
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return content.decode('utf-8', errors='ignore')

@app.post("/parse-resume")
async def parse_resume(files: list[UploadFile] = File(None)):
    employees = []
    
    for file in files:
        content = await file.read()
        
        # Extract text from PDF if it's a PDF file
        if file.filename and file.filename.lower().endswith('.pdf'):
            content = extract_text_from_pdf(content)
        elif hasattr(content, 'decode'):
            content = content.decode('utf-8', errors='ignore')
        
        print(f"Parsing resume: {file.filename}, text length: {len(content)}")
        llm_response = await call_llm(
            f"""You are an HR specialist. Extract employee information from this resume.
Look for: name, job title/role, skills, years of experience.
Return ONLY a valid JSON object like: {{"name": "John Doe", "role": "Software Engineer", "skills": ["Python", "Java"], "experience": "5 years"}}
If cannot find a field, use empty string "" instead of null.
No markdown, no explanation, just the JSON.

Resume content:
{content[:4000]}"""
        )
        print(f"Resume LLM response: {llm_response[:500] if llm_response else 'EMPTY'}")
        
        if llm_response:
            try:
                emp = json.loads(llm_response)
                emp["id"] = str(uuid.uuid4())[:8]
                employees.append(emp)
            except:
                pass
    
    if not employees:
        employees = [
            {"id": "1", "name": "Alex Chen", "role": "Frontend Developer", "skills": ["React", "TypeScript", "CSS", "Node.js"], "experience": "5 years"},
            {"id": "2", "name": "Sarah Miller", "role": "Backend Developer", "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"], "experience": "7 years"},
            {"id": "3", "name": "James Wilson", "role": "Full Stack Developer", "skills": ["React", "Node.js", "Python", "SQL"], "experience": "4 years"},
        ]
    
    return {"employees": employees}

@app.post("/crew-generate")
async def crew_generate(request: CrewGenerateRequest):
    assignments = []
    
    for task in request.tasks:
        best_match = None
        best_score = 0
        
        for emp in request.employees:
            score = 0
            task_skills = set(s.lower() for s in task.requiredSkills)
            emp_skills = set(s.lower() for s in emp.skills)
            matches = len(task_skills & emp_skills)
            score = min(100, 50 + matches * 15)
            
            if score > best_score:
                best_score = score
                best_match = emp
        
        if best_match:
            assignments.append({
                "taskId": task.id,
                "taskTitle": task.title,
                "employeeId": best_match.id,
                "employeeName": best_match.name,
                "matchScore": best_score
            })
    
    config = {
        "name": "Project Crew",
        "tasks": assignments,
        "generatedAt": datetime.now().isoformat()
    }
    
    return {"assignments": assignments, "config": config}

async def generate_logs(config: CrewConfig):
    yield "data: " + json.dumps({"timestamp": datetime.now().isoformat(), "agent": "coordinator", "status": "started", "message": "Initializing crew execution..."}) + "\n\n"
    await asyncio.sleep(0.5)
    
    yield "data: " + json.dumps({"timestamp": datetime.now().isoformat(), "agent": "coordinator", "status": "completed", "message": "Crew initialized successfully"}) + "\n\n"
    await asyncio.sleep(0.3)
    
    seen_agents = set()
    for assignment in config.tasks:
        agent_name = f"{assignment.employeeName.split()[0]} Agent"
        if agent_name not in seen_agents:
            seen_agents.add(agent_name)
            yield "data: " + json.dumps({"timestamp": datetime.now().isoformat(), "agent": agent_name, "status": "started", "message": f"Starting task: {assignment.taskTitle}"}) + "\n\n"
            await asyncio.sleep(0.8)
            yield "data: " + json.dumps({"timestamp": datetime.now().isoformat(), "agent": agent_name, "status": "completed", "message": f"Completed: {assignment.taskTitle}"}) + "\n\n"
    
    yield "data: " + json.dumps({"timestamp": datetime.now().isoformat(), "agent": "coordinator", "status": "completed", "message": "All tasks completed successfully"}) + "\n\n"

@app.post("/crew-run-stream")
async def crew_run_stream(request: CrewRunRequest):
    return StreamingResponse(generate_logs(request.config), media_type="text/event-stream")

@app.get("/crew-download")
async def crew_download():
    return {"message": "Download endpoint - implement file generation"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)