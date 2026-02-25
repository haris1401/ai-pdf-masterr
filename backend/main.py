from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import models
from models import SessionLocal, engine, Agent, Task, Metric
import agents
import threading
import time
import asyncio

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models
class TaskCreate(BaseModel):
    description: str
    agent_type: str

class TaskResponse(BaseModel):
    id: int
    description: str
    status: str
    result: Optional[str]
    created_at: str
    agent_id: int

    class Config:
        from_attributes = True

# Initialize Agents
def initialize_agents(db: Session):
    agent_types = ["sales", "support", "operations"]
    for agent_type in agent_types:
        agent = db.query(Agent).filter(Agent.type == agent_type).first()
        if not agent:
            new_agent = Agent(name=f"{agent_type.capitalize()} Agent", type=agent_type, status="idle")
            db.add(new_agent)
            db.commit()

# Background Worker
def process_tasks():
    while True:
        db = SessionLocal()
        try:
            # Find pending tasks
            pending_tasks = db.query(Task).filter(Task.status == "pending").all()
            
            for task in pending_tasks:
                agent_model = db.query(Agent).filter(Agent.id == task.agent_id).first()
                if agent_model:
                    # Instantiate the appropriate agent class
                    if agent_model.type == "sales":
                        agent_logic = agents.SalesAgent(db, agent_model)
                    elif agent_model.type == "support":
                        agent_logic = agents.SupportAgent(db, agent_model)
                    elif agent_model.type == "operations":
                        agent_logic = agents.OperationsAgent(db, agent_model)
                    else:
                        continue

                    # Process the task
                    try:
                        # Update task status to in_progress
                        task.status = "in_progress"
                        db.commit()
                        
                        agent_logic.process_task(task)
                    except Exception as e:
                        print(f"Error processing task {task.id}: {e}")
                        task.status = "failed"
                        task.result = str(e)
                        db.commit()
            
        except Exception as e:
            print(f"Error in worker loop: {e}")
        finally:
            db.close()
        
        time.sleep(2)  # Check every 2 seconds

# Start background worker on startup
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    initialize_agents(db)
    db.close()
    
    # Start worker thread
    worker_thread = threading.Thread(target=process_tasks, daemon=True)
    worker_thread.start()

# API Endpoints

@app.get("/agents")
def get_agents(db: Session = Depends(get_db)):
    return db.query(Agent).all()

@app.get("/tasks")
def get_tasks(db: Session = Depends(get_db)):
    return db.query(Task).order_by(Task.created_at.desc()).limit(20).all()

@app.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    return db.query(Metric).order_by(Metric.timestamp.desc()).limit(20).all()

@app.post("/tasks")
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    # Find agent
    agent = db.query(Agent).filter(Agent.type == task.agent_type).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    new_task = Task(description=task.description, agent_id=agent.id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

# Mount static files
app.mount("/", StaticFiles(directory="static", html=True), name="static")
