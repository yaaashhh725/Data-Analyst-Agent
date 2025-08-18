import os
import sys
import json
import subprocess
import ast
import requests
import shutil
import re
# Import our dummy agents
import code_generator_agent
import debugger_agent
import vision_agent

class DependencyError(Exception):
    """Custom exception for dependency issues."""
    pass

class TaskOrchestrator:
    """
    Manages the entire workflow from planning to execution and debugging.
    """
    def __init__(self, plan_data):
        if isinstance(plan_data, str):
            self.plan = json.loads(plan_data)
        # If it's already a list/dict (Python object), use it directly
        else:
            self.plan = plan_data
        self.work_dir = "session_workspace"
        self.max_retries = 3 # 1 initial attempt + 3 retries
        
        # Clean up previous session if it exists
        # if os.path.exists(self.work_dir):
        #     shutil.rmtree(self.work_dir)
        os.makedirs(self.work_dir, exist_ok=True)
        print(f"Workspace created at: {os.path.abspath(self.work_dir)}")

    def extract_python_code(self,llm_output: str) -> str:
        """
        Extracts Python code from an LLM's output string.
        It handles code wrapped in ```python ... ```, ``` ... ```,
        or raw code.
        """
        # Pattern to find code blocks with or without the 'python' language tag
        pattern = r"```(?:python\n)?(.*?)```"
        
        match = re.search(pattern, llm_output, re.DOTALL)
        if match:
            # If a markdown code block is found, return its content
            return match.group(1).strip()
        else:
            # If no markdown block is found, assume the whole output is code
            return llm_output.strip()

    def _parse_imports(self, code: str) -> set:
        """Parses code to find all top-level imports using AST."""
        try:
            tree = ast.parse(code)
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])
            return imports
        except SyntaxError as e:
            print(f"Error parsing code for imports: {e}")
            return set()

    def _check_and_install_dependencies(self, code: str):
        """Checks for required imports and installs them if they are valid and missing."""
        imports = self._parse_imports(code)
        if not imports:
            return
            
        print(f"Found potential dependencies: {imports}")
        for package in imports:
            try:
                # Check if the package is already available
                __import__(package)
                print(f"Dependency '{package}' is already installed.")
            except ImportError:
                print(f"Dependency '{package}' not found. Verifying with PyPI...")
                # Verify with PyPI to avoid installing hallucinated packages
                response = requests.get(f"https://pypi.org/pypi/{package}/json")
                if response.status_code == 200:
                    print(f"'{package}' is a valid package. Installing...")
                    # Use sys.executable to ensure pip is from the correct env
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", package],
                        check=True, capture_output=True, text=True
                    )
                    print(f"Successfully installed '{package}'.")
                else:
                    raise DependencyError(f"LLM hallucinated a non-existent package: '{package}'")

    def execute_workflow(self) -> dict:
        """Executes the entire plan, task by task."""
        last_task_output = ""
        last_error = ""
        for task in self.plan:
            task_id = task.get("task_id")
            print(f"\n{'='*20} EXECUTING TASK {task_id} {'='*20}")
            print(f"Description: {task.get('description')}")

            tool = task.get('tool_needed')
            if tool not in ['python', 'vision']:
                print(f"Unsupported tool: {tool}")
                continue
            
            if tool.lower() == 'python':
                current_code = ""
                
                is_successful = False

                for attempt in range(self.max_retries + 1):
                    print(f"\n--- Attempt {attempt + 1} of {self.max_retries + 1} ---")
                    
                    # 1. Generate or Debug Code
                    if attempt == 0:
                        llm_code = code_generator_agent.generate_code(task ,last_task_output)
                        if llm_code == '' or llm_code is None:
                            print("Code generation failed.")
                            continue

                        current_code = self.extract_python_code(llm_code)
                    else:
                        # Pass the error to the debugger for a fix
                        llm_code = debugger_agent.debug_code(task,last_task_output, current_code, last_error)
                        current_code = self.extract_python_code(llm_code)

                    # 2. Check Dependencies
                    try:
                        self._check_and_install_dependencies(current_code)
                    except DependencyError as e:
                        print(f"FATAL ERROR: {e}")
                        return {"status": "failed", "reason": str(e)}

                    # 3. Execute Code
                    script_path = os.path.join(os.path.abspath(self.work_dir), "script.py")
                    print(script_path,'-----------------------------------')
                    with open(script_path, "w") as f:
                        f.write(current_code)

                    result = subprocess.run(
                        [sys.executable, script_path],
                        capture_output=True, text=True, cwd=self.work_dir
                    )

                    # 4. Check Result
                    if result.returncode == 0:
                        print(f"--- Task {task_id} SUCCEEDED on attempt {attempt + 1}. ---")
                        print("Output:\n", result.stdout)

                        last_task_output = last_task_output + f'{task_id} output: \n{result.stdout.strip()}'

                        is_successful = True
                        break
                    else:
                        print(f"--- Task {task_id} FAILED on attempt {attempt + 1}. ---")
                        last_error = result.stderr
                        print("Error:\n", last_error)
                
                if not is_successful:
                    print(f"\nFATAL: Task {task_id} failed after all retries. Aborting workflow.")
                    return {
                        "status": "failed",
                        "failed_task_id": task_id,
                        "last_error": last_error
                    }

            elif tool.lower() == 'vision':
                is_successful = False

                input_artifacts = task.get('input_artifacts', [])
                input_artifacts = [os.path.join(self.work_dir, artifact) for artifact in input_artifacts]
                output_filename = task.get('output_artifacts')[0]  # Get the first output artifact
                task_description = task.get('description', 'Give a short description of the image and write all the text present in the image.')
                for attempt in range(self.max_retries + 1):
                    print(f"\n--- Attempt {attempt + 1} of {self.max_retries + 1} ---")

                    vision_analysis = vision_agent.visual_analysis(input_artifacts, task_description)
                    if vision_analysis==None or vision_analysis == '':
                        print("Vision analysis failed. Try again")

                    if vision_analysis:
                        with open(os.path.join(self.work_dir, output_filename), "w") as f:
                            f.write(vision_analysis)
                        print(f"Vision analysis succeeded. Output written to {output_filename}")
                        is_successful = True
                        break

                if not is_successful:
                    print(f"\nFATAL: Task {task_id} failed after all retries. Aborting workflow.")
                    return {
                        "status": "failed",
                        "failed_task_id": task_id,
                        "last_error": last_error
                    }


        # 5. Finalize
        print("\n{'='*20} WORKFLOW COMPLETED SUCCESSFULLY {'='*20}")
        final_output_path = os.path.join(self.work_dir, "final_output.json")
        if os.path.exists(final_output_path):
            with open(final_output_path, "r") as f:
                return json.load(f)
        else:
            return {"status": "success", "reason": "Workflow finished but final_output.json was not found."}


    # destructor to delete the session_workspace folder
    def __del__(self):
        print(f"Cleaning up workspace: {self.work_dir}")
        shutil.rmtree(self.work_dir, ignore_errors=True)

# if __name__ == "__main__":
#     # This is the JSON plan produced by the "Planner" LLM.
#     # It describes the multi-step process to achieve the user's goal.
#     PLAN_JSON = """
#     [
#       {
#         "task_id": 1,
#         "description": "Create an initial dummy dataset of movies and ranks.",
#         "tool_needed": "python",
#         "dependencies": [],
#         "input_artifacts": [],
#         "output_artifacts": ["task_1_movies.parquet"]
#       },
#       {
#         "task_id": 2,
#         "description": "Load the movie data and calculate the average rank.",
#         "tool_needed": "python",
#         "dependencies": [1],
#         "input_artifacts": ["task_1_movies.parquet"],
#         "output_artifacts": ["task_2_average_rank.json"]
#       },
#       {
#         "task_id": 3,
#         "description": "Load all intermediate results and assemble the final output JSON.",
#         "tool_needed": "python",
#         "dependencies": [1, 2],
#         "input_artifacts": ["task_2_average_rank.json", "task_1_movies.parquet"],
#         "output_artifacts": ["final_output.json"]
#       }
#     ]
#     """

#     orchestrator = TaskOrchestrator(PLAN_JSON)
#     final_result = orchestrator.execute_workflow()

#     print("\n\n--- FINAL WORKFLOW RESULT ---")
#     print(json.dumps(final_result, indent=2))
