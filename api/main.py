from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
from main_agent import task_breakdown
from orchestrator import TaskOrchestrator
import subprocess
import os
import sys
import shutil
import json

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

# @app.post("/upload")
# async def upload_files(files: List[UploadFile] = File(...)):
#     names = []
#     for file in files:
#         content = await file.read()  # Read file content
#         print(content)
#         names.append(file.filename)

#     return {'message': f'Uploaded {names} files successfully!'}
@app.post("/upload")
async def upload_files(files: Optional[List[UploadFile]] = File(None)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    questions = None

    extra_files = []

    for file in files:
        if not file.filename :
            continue
            
        if file.filename == 'questions.txt':
            # read the questions.txt and call the main agent to make task plan
            questions = (await file.read()).decode()
            continue

        # Create directory if it doesn't exist
        os.makedirs("session_workspace", exist_ok=True)
        
        # Save file to disk
        file_path = f"session_workspace/{file.filename}"
        extra_files.append(file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Close the file to free up resources
        file.file.close()
    
    if not questions:
        # return 400 response that file not found
        raise HTTPException(status_code=400, detail="questions.txt is either empty or missing")
    
    # Process files here as needed
    questions = questions + f"Files provided with the questions.txt are: {''.join(extra_files)}"
    # call the main agent to create plan for the questions file.
    # task = task_breakdown(questions)
    # # with open('tasks.json','w') as f:
    # #     f.write(task)
    
    # orchestrator = TaskOrchestrator(task)
    # final_result = orchestrator.execute_workflow()
    
    # return final_result
    try:
        task = task_breakdown(questions)
    except Exception as e:
        print(f"task_breakdown failed: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail="Planner failed. Check GEMINI_API_KEY and logs.")

    try:
        orchestrator = TaskOrchestrator(task)
        final_result = orchestrator.execute_workflow()
        orchestrator.__del__()
        return final_result
    except Exception as e:
        print(f"execute_workflow failed: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail="Internal server error during task execution")
    # print(final_result)
    # print(type(final_result))

@app.get("/debug")
async def debug():
    return {
        "current_dir": os.getcwd(),
        "files_in_current_dir": os.listdir("."),
        "absolute_path_of_api_dir": os.path.abspath("."),
        "python_executable": sys.executable,
        "sys_path": sys.path[:5],  # First 5 paths
    }

@app.get("/final-result")
async def final_result():

    path = os.path.join(os.getcwd(),'session_workspace', 'final_output.json')
    with open(path) as f:
        final_result = json.load(f)
    return final_result

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
    question = """Scrape the list of highest grossing films from Wikipedia. It is at the URL:
https://en.wikipedia.org/wiki/List_of_highest-grossing_films

Answer the following questions and respond with a JSON array of strings containing the answer.

1. How many $2 bn movies were released before 2000?
2. Which is the earliest film that grossed over $1.5 bn?
3. What's the correlation between the Rank and Peak?
4. Draw a scatterplot of Rank and Peak along with a dotted red regression line through it.
   Return as a base-64 encoded data URI, `"data:image/png;base64,iVBORw0KG..."` under 100,000 bytes.
"""
    try:
        tasks = task_breakdown(question)
        # save the tasks into tasks.json
        # with open("tasks.json", "w") as f:
        #     f.write(tasks)
        return {"tasks": tasks}
    except Exception as e:
        return {"error": str(e)}

# don't include this for vercel deployment
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    #for render deployment 0.0.0.0 host