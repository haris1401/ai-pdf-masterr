from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///./ai_console.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String)  # 'sales', 'support', 'operations'
    status = Column(String, default="idle")  # 'idle', 'busy', 'error'
    last_active = Column(DateTime, default=datetime.utcnow)

    tasks = relationship("Task", back_populates="agent")
    metrics = relationship("Metric", back_populates="agent")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    status = Column(String, default="pending")  # 'pending', 'in_progress', 'completed', 'failed'
    result = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    agent_id = Column(Integer, ForeignKey("agents.id"))

    agent = relationship("Agent", back_populates="tasks")

class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"))
    metric_name = Column(String)
    value = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

    agent = relationship("Agent", back_populates="metrics")

def init_db():
    Base.metadata.create_all(bind=engine)
