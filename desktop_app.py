import os
import sys
import time
import threading
import webbrowser
import uvicorn
import subprocess

def run_desktop_app():
    # Get the project root and backend directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(project_root, 'backend')
    
    # Change working directory to backend so that relative paths (like static files) work
    os.chdir(backend_dir)
    sys.path.append(backend_dir)
    
    # Import app after changing directory and updating sys.path
    try:
        from main import app
    except ImportError as e:
        print(f"Error importing app: {e}")
        return

    # Define server runner
    def start_server():
        uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")

    # Start server in a separate thread
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()

    print("Server starting on http://127.0.0.1:8001...")
    
    # Wait for server to initialize
    time.sleep(2)

    url = "http://127.0.0.1:8001"
    
    # Attempt to open in App Mode (Chrome/Edge)
    opened_in_app_mode = False
    
    # Common browser paths on Windows
    browser_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ]
    
    for path in browser_paths:
        if os.path.exists(path):
            try:
                print(f"Launching {path} in App Mode...")
                subprocess.Popen([path, f"--app={url}"])
                opened_in_app_mode = True
                break
            except Exception as e:
                print(f"Failed to launch {path}: {e}")
    
    if not opened_in_app_mode:
        print("Could not find Edge or Chrome for App Mode. Opening default browser...")
        webbrowser.open(url)

    # Keep the main thread alive to let the server run
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping AI Console...")

if __name__ == "__main__":
    run_desktop_app()
