from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

