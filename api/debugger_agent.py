# To run this code you need to install the following dependencies:
# pip install google-genai

import json
import base64
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()

def debug_code(task: dict, failed_code: str, error_message: str) -> str:
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.0-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=f"""### ORIGINAL TASK
{task}

---
### FAILED PYTHON SCRIPT
{failed_code}

---
### EXECUTION ERROR TRACEBACK
{error_message}
"""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        system_instruction=[
            types.Part.from_text(text="""### ROLE AND GOAL
You are a world-class, automated Python debugging service. Your sole purpose is to receive a Python script that has failed, analyze the error, and provide a fully corrected version of the script that is ready for immediate re-execution.

---
### INPUTS
You will be provided with the following three pieces of information:

1.  **ORIGINAL TASK:** The high-level description of what the script was supposed to accomplish.
2.  **FAILED PYTHON SCRIPT:** The complete source code that resulted in an error.
3.  **EXECUTION ERROR TRACEBACK:** The full standard error output (`stderr`) from the failed execution, which includes the error type and traceback.

---
### ANALYTICAL PROCESS (Your Thought Process)
Before writing any code, you must internally follow these steps:
1.  **Analyze the Traceback:** Pinpoint the exact line number, error type (e.g., `KeyError`, `FileNotFoundError`, `TypeError`), and error message from the traceback.
2.  **Identify the Root Cause:** Based on the error and the surrounding code in the `FAILED SCRIPT`, determine the logical reason for the failure. (e.g., \"The code is trying to access a dictionary key 'ratings' that does not exist. The available keys are 'rank' and 'movie_title'.\")
3.  **Formulate a Correction Plan:** Decide on the minimal, correct change required to fix the bug while preserving the script's original intent as described in the `ORIGINAL TASK`.

---
### CORE INSTRUCTIONS
* **Implement the Fix:** Apply your correction plan to the `FAILED PYTHON SCRIPT`.
* **Return the Complete Script:** Your output **MUST** be the entire, fully corrected Python script from top to bottom. Do not provide only the changed lines or a patch.
* **Preserve Original Intent:** The corrected script must still achieve the `ORIGINAL TASK`'s goal. It must use the same input and output file paths that were defined in the failed script.
* **Maintain Best Practices:** Ensure the corrected code is clean, readable, and continues to follow any best practices mentioned in the original code (like logging progress with `print` statements).

---
### OUTPUT SPECIFICATION
* Your response **MUST BE THE RAW PYTHON CODE ONLY.**
* **DO NOT** wrap the code in markdown backticks (e.g., \\`\\`\\`python).
* **DO NOT** include any text, explanations, apologies, or comments before or after the code. Your entire output will be saved directly to a `.py` file and executed.
"""),
        ],
    )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
    # print(response.text)
    return response.text
    # for chunk in client.models.generate_content_stream(
    #     model=model,
    #     contents=contents,
    #     config=generate_content_config,
    # ):
    #     print(chunk.text, end="")

# if __name__ == "__main__":
#     task = '''{
#         "task_id": 2,
#         "description": "Load the movie data and calculate the average rank.",
#         "tool_needed": "python",
#         "dependencies": [1],
#         "input_artifacts": ["task_1_movies.parquet"],
#         "output_artifacts": ["task_2_average_rank.json"]
#       }'''
#     failed_code = '''
# import pandas as pd
# import json

# movies = pd.read_parquet("task_1_movies.csv")  

# average_rank = movies["rank"].sum() / (len(movies) + 1)

# with open("task_2_average_rank.json", "w") as f:
#     json.dump({"average": str(average_rank)}, f)  
# '''
#     error = '''
# Traceback (most recent call last):
#   File "D:\data_analyst_agent\session_workspace\script.py", line 4, in <module>
#     movies = pd.read_parquet("task_1_movies.csv")
#   File "D:\data_analyst_agent\.venv\Lib\site-packages\pandas\io\parquet.py", line 669, in read_parquet
#     return impl.read(
#            ~~~~~~~~~^
#         path,
#         ^^^^^
#     ...<6 lines>...
#         **kwargs,
#         ^^^^^^^^^
#     )
#     ^
#   File "D:\data_analyst_agent\.venv\Lib\site-packages\pandas\io\parquet.py", line 398, in read
#     handles = get_handle(
#         path, "rb", is_text=False, storage_options=storage_options
#     )
#   File "D:\data_analyst_agent\.venv\Lib\site-packages\pandas\io\common.py", line 882, in get_handle
#     handle = open(handle, ioargs.mode)
# FileNotFoundError: [Errno 2] No such file or directory: 'task_1_movies.csv'
# '''
#     debug_code(task,failed_code, error)

