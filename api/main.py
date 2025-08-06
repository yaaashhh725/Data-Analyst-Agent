from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from main_agent import task_breakdown
import subprocess
import os
import sys

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"]) # Allow GET requests from all origins
# Or, provide more granular control:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all domains
    allow_credentials=True,  # Allow cookies
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Allow specific methods
    allow_headers=["*"],  # Allow all headers
)

@app.get("/")
async def home():
    return {"message": "Welcome to the FastAPI application!"}

@app.get("/debug")
async def debug():
    return {
        "current_dir": os.getcwd(),
        "files_in_current_dir": os.listdir("."),
        "absolute_path_of_api_dir": os.path.abspath("."),
        "python_executable": sys.executable,
        "sys_path": sys.path[:5],  # First 5 paths
    }


@app.get("/run-script")
async def run_script():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(current_dir, 'try.py')
    result = subprocess.run(['python', script_path], capture_output=True, text=True)
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    }

@app.get("/task-breakdown")
async def task_breakdown_endpoint():
    """
    Endpoint to break down a task based on the provided question.
    """
    question = """The undirected network in [`edges.csv`](./project-data-analyst-agent-sample-network/edges.csv) lists edges between five people.
7. Plot the degree distribution as a bar chart with green bars. Encode as a base64 PNG under 100,000 bytes."""
    try:
        tasks = task_breakdown(question)
        return tasks
    except Exception as e:
        return {"error": str(e)}

# don't include this for vercel deployment
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000)