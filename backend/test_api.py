import requests
import time

BASE_URL = "http://localhost:8000"

def test_create_task():
    print("Creating Sales Task...")
    response = requests.post(f"{BASE_URL}/tasks", json={
        "description": "Reach out to lead: Alice",
        "agent_type": "sales"
    })
    print("Create Response:", response.status_code, response.json())
    assert response.status_code == 200
    task_id = response.json()["id"]
    return task_id

def test_check_status(task_id):
    print(f"Checking status for task {task_id}...")
    for _ in range(5):
        response = requests.get(f"{BASE_URL}/tasks")
        tasks = response.json()
        for task in tasks:
            if task["id"] == task_id:
                print(f"Task Status: {task['status']}, Result: {task.get('result')}")
                if task["status"] == "completed":
                    return
        time.sleep(1)

if __name__ == "__main__":
    task_id = test_create_task()
    test_check_status(task_id)
