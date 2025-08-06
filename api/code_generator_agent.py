# To run this code you need to install the following dependencies:
# pip install google-genai

import base64
import os
from google import genai
from google.genai import types
import json
from dotenv import load_dotenv 
load_dotenv()  # Load environment variables from .env file

def generate_code(task: dict) -> str:
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.0-flash-lite"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=f"""Task details: Description: {task.get('description')}, Input artifacts: {task.get('input_artifacts')}, Output artifacts: {task.get('output_artifacts')}"""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        system_instruction=[
            types.Part.from_text(text="""ROLE AND GOALYou are an expert-level Python data engineer. Your sole purpose is to write a clean, efficient, and self-contained Python script to accomplish a single, specific task. You will be given a task description and a list of input and output files. Your generated script will be executed in a new, isolated environment.CONTEXT & ENVIRONMENTStateless Execution: The script will be run independently. It cannot access any variables, data, or state from previously executed scripts. All necessary data must be loaded from the specified input files.File-Based State: The only way to pass data to subsequent tasks is by saving it to the specified output files.Available Libraries: Assume a standard data science environment is available with pandas, pyarrow, duckdb, numpy, scikit-learn, and requests already installed.CORE INSTRUCTIONS & BEST PRACTICESUse Parquet, Not CSV: For all operations involving pandas DataFrames, you MUST use the Parquet file format for both reading (pd.read_parquet()) and writing (df.to_parquet()). Parquet is faster and preserves data types. Do not use CSV.Use DuckDB for SQL: If the task requires running SQL queries on files (like Parquet or CSV), you MUST use the duckdb Python library. Execute the query and fetch the results into a pandas DataFrame. For example: df = duckdb.sql('SELECT * FROM \"path/to/file.parquet\"').df().Strict Input/Output:Your script MUST read data only from the files listed in the input_artifacts.Your script MUST save its results only to the files listed in the output_artifacts.The file paths provided are relative to the script's execution directory.Robust Code:Import all necessary libraries at the top of the script.Include print statements to log the script's progress (e.g., \"Loading data from file.parquet...\", \"Calculation complete. Saving output...\"). This is crucial for debugging.Anticipate potential errors. For example, when converting data types, handle possible exceptions.Clarity and Simplicity: Write straightforward, readable code. Add comments only for complex logic. Do not create overly complex functions or classes for a simple task.OUTPUT SPECIFICATIONYour response MUST be only the raw Python code for the script.Do NOT wrap the code in markdown backticks (e.g., ```python).Do NOT add any explanations, introductions, or conclusions. Your entire output will be saved directly to a .py file and executed."""),
        ],
    )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
    return response.text
    # for chunk in client.models.generate_content(
    #     model=model,
    #     contents=contents,
    #     config=generate_content_config,
    # ):
    #     print(chunk.text, end="")

# if __name__ == "__main__":
#     task = json.loads('''{
#         "task_id": 1,
#         "description": "Create an initial dummy dataset of movies and ranks.",
#         "tool_needed": "python",
#         "dependencies": [],
#         "input_artifacts": [],
#         "output_artifacts": ["task_1_movies.parquet"]
#       }''')
#     generate_code(task)