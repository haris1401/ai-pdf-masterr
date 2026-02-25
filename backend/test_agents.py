import requests
import time

BASE_URL = "http://localhost:8000"

def create_task(description, agent_type):
    print(f"Creating {agent_type} Task: {description}")
    response = requests.post(f"{BASE_URL}/tasks", json={
        "description": description,
        "agent_type": agent_type
    })
    print("Create Response:", response.status_code)
    return response.json()["id"]

def check_status(task_id):
    print(f"Checking status for task {task_id}...")
    for _ in range(10):
        response = requests.get(f"{BASE_URL}/tasks")
        tasks = response.json()
        for task in tasks:
            if task["id"] == task_id:
                print(f"Task Status: {task['status']}, Result: {task.get('result')}")
                if task["status"] == "completed":
                    return
        time.sleep(1)

if __name__ == "__main__":
    # Test Sales Agent
    sales_task_id = create_task("Pricing query for enterprise plan", "sales")
    check_status(sales_task_id)

    # Test Support Agent
    support_task_id = create_task("Check ticket status #123", "support")
    check_status(support_task_id)

    # Test Operations Agent
    ops_task_id = create_task("Check SLA status", "operations")
    check_status(ops_task_id)
