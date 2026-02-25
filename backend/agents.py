from models import Agent, Task, Metric
from datetime import datetime
import time
import random

class BaseAgent:
    def __init__(self, db_session, agent_model):
        self.db = db_session
        self.agent = agent_model

    def update_status(self, status):
        self.agent.status = status
        self.agent.last_active = datetime.utcnow()
        self.db.commit()

    def log_metric(self, name, value):
        metric = Metric(agent_id=self.agent.id, metric_name=name, value=value)
        self.db.add(metric)
        self.db.commit()

class SalesAgent(BaseAgent):
    def process_task(self, task):
        self.update_status("busy")
        print(f"Sales Agent processing task: {task.description}")
        
        # Simulate work
        time.sleep(2)
        
        description = task.description.lower()
        if "reach out" in description or "lead" in description:
            result = "Reached out to inbound lead. Initial contact email sent."
        elif "pricing" in description:
            result = "Pricing query answered: Our enterprise plan starts at $99/mo."
        elif "product" in description:
            result = "Product query answered: Features include AI automation and real-time analytics."
        elif "purchase" in description or "schedule" in description:
            result = "Customer interested in purchase. Appointment scheduled for demo."
        else:
            result = "Task processed: General sales inquiry handled."
            
        task.result = result
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        self.db.commit()
        
        self.log_metric("sales_activities", 1)
        self.update_status("idle")
        return result

class SupportAgent(BaseAgent):
    def process_task(self, task):
        self.update_status("busy")
        print(f"Support Agent processing task: {task.description}")
        
        time.sleep(2)
        
        description = task.description.lower()
        if "product" in description:
            result = "Product query answered: Please refer to the user manual section 3.2."
        elif "ticket" in description and "update" in description:
            result = "Fetched ticket update: Ticket #404 is currently being reviewed by engineering."
        elif "unresolved" in description or "issue" in description:
            result = "Issue unresolved. Created new support ticket #505."
        else:
            result = "Support query processed: Standard troubleshooting steps provided."
            
        task.result = result
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        self.db.commit()
        
        self.log_metric("tickets_processed", 1)
        self.update_status("idle")
        return result

class OperationsAgent(BaseAgent):
    def process_task(self, task):
        self.update_status("busy")
        print(f"Operations Agent processing task: {task.description}")
        
        time.sleep(2)
        
        description = task.description.lower()
        if "sla" in description:
            result = "SLA Monitor: Current uptime 99.98%. Response time within limits."
        elif "error" in description:
            result = "Error Report: 500 Internal Server Error detected in log stream."
        elif "manage" in description or "task" in description:
            result = "Task Management: Reallocated server resources for peak load."
        else:
            result = "Operations task completed: System check passed."
            
        task.result = result
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        self.db.commit()
        
        self.log_metric("ops_checks", 1)
        self.update_status("idle")
        return result
