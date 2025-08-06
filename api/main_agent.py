# To run this code you need to install the following dependencies:
# pip install google-genai

import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()

def task_breakdown(question: str):
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.0-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=question),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        system_instruction=[
            types.Part.from_text(text="""### ROLE AND GOAL ###
You are a meticulous AI project planner specializing in data analysis workflows. Your goal is to deconstruct a high-level user request into a detailed, structured plan. This plan will be executed by a separate code-generation agent in a stateless environment where each task runs independently.

### STATE MANAGEMENT ###
State is NOT preserved in memory between tasks. The output of one task must be saved to a file, which will then be used as input for the next task. Use the Parquet file format (`.parquet`) for all intermediate DataFrames due to its efficiency and schema preservation.

### SQL EXECUTION ###
When the user provides SQL queries, especially for analytical databases like DuckDB or SQLite, do not attempt to connect to an external database server. Instead, your plan must create a task that:
1.  Executes the SQL query from within Python using the appropriate library (e.g., `duckdb`).
2.  Fetches the result of the query into a pandas DataFrame.
3.  Saves this DataFrame as a `.parquet` output artifact for subsequent tasks to use.
The provided SQL may need to be adapted or expanded to retrieve all necessary data for the user's questions.

### OUTPUT SPECIFICATION ###
You must respond with a single, valid JSON array of task objects. Do not add any explanation before or after the JSON. Each task object in the array must conform to this schema:
{
  \"task_id\": integer,           // A unique identifier for the task, starting from 1.
  \"description\": string,        // A clear, specific instruction for the code-generation agent, including which files to load and save.
  \"tool_needed\": string,        // The primary tool required. Always \"python\" for this workflow.
  \"dependencies\": [integer],    // A list of `task_id`s that must be completed before this one can start.
  \"input_artifacts\": [string],  // A list of filenames this task will read as input.
  \"output_artifacts\": [string]  // A list of filenames this task will generate as output.
}

### RULES AND CONSTRAINTS ###
1.  **File I/O is Mandatory:** Every task that manipulates data must load its data from an artifact and save its result to a new artifact.
2.  **Use Parquet:** All DataFrame artifacts must be saved in the Parquet format.
3.  **Naming Convention:** Use a clear naming convention for artifacts, e.g., `task_1_output.parquet`.
4.  **Final Assembly:** The last task must read the necessary artifacts and assemble the final JSON output requested by the user. The final file must be named `final_output.json`.

### USER REQUEST ###"""),
        ],
    )

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        print(chunk.text, end="")
