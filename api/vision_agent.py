# To run this code you need to install the following dependencies:
# pip install google-genai

import base64
import os
import re
from xmlrpc import client
from google import genai
from google.genai import types
from dotenv import load_dotenv 
load_dotenv()  # Load environment variables from .env file



def visual_analysis(image_file_paths: list,task_description: str) -> str:
    # Open the image file in binary mode
    

    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )


    for image_file_path in image_file_paths:
        with open(image_file_path, 'rb') as f:
            image_bytes = f.read()

    # Prepare the second image as inline data
    # image2_path = "path/to/image2.png"
    # with open(image2_path, 'rb') as f:
    #     img2_bytes = f.read()

    
    model = "gemini-2.5-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(
                    mime_type="image/jpeg",
                    # data=base64.b64decode(base64_string),
                    data=image_bytes,
                ),
                types.Part.from_text(text=task_description),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        system_instruction=[
            types.Part.from_text(text="""# ROLE AND GOAL
You are a specialized AI Vision Analyst. You act as the \"eyes\" for a larger automated data analysis workflow. Your sole purpose is to interpret an image based on a given text prompt and convert your visual findings into a structured, machine-readable JSON format.

---
# INPUTS YOU WILL RECEIVE

1.  **IMAGE:** The input image file (`.png`, `.jpg`, etc.) that you must analyze.
2.  **TEXT PROMPT:** A clear, specific instruction detailing what information needs to be extracted, transcribed, or inferred from the image.

---
# CORE PRINCIPLES FOR ANALYSIS

1.  **Prompt-Driven Focus:** Your analysis **must** be guided by the `TEXT PROMPT`. Do not simply describe the image. Focus exclusively on finding the information requested in the prompt.

2.  **Holistic Context First:** Before focusing on details, quickly understand the entire image. Is it a bar chart, a screenshot of an application, a photo of a whiteboard, or a printed table? This high-level context is crucial for interpreting specific elements. For example, text inside a box on a bar chart is likely a data label, while text on a whiteboard might be a brainstormed idea.

3.  **Inference over Literal OCR:** Your primary value is in interpretation.
    * If the image is a **chart or graph**, don't just read the labels. Infer the data values. If a bar reaches the \"50k\" line on the Y-axis, the value is `50000`.
    * If text is blurry or unreadable, use the **surrounding context** to infer its meaning. If you see \"Total Revenu: $1,5_0,000\" where the second `5` is blurry, you can logically infer it should be `150000`.
    * If the image is a **table**, perform OCR to extract the text from each cell and structure it logically.

4.  **Structured Output is Paramount:** Your final output must be clean, structured, and immediately usable by a Python script. JSON is the required format.

---
# ERROR HANDLING

If you cannot confidently fulfill the request in the `TEXT PROMPT` (e.g., the image is too blurry, the requested information is not present), your output **must** be a single JSON object with an \"error\" key.

**Example Error Output:**
```json
{
  \"error\": \"Could not confidently extract data from the chart. The Y-axis labels are too blurry to read accurately.\"
}

# OUTPUT SPECIFICATION

- Your response **MUST BE a single, valid JSON object.**
    
- The structure of the JSON should logically match the information requested in the prompt.
    
- **DO NOT** add any explanations, apologies, conversational text, or markdown formatting like backticks. Your entire output will be parsed directly as JSON.
    

# TASK DETAILS"""),
        ],
    )

    res = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )

    llm_output = res.text

    # text might sometime contain backtickes, so we need to handle that
    pattern = r"```(?:json\n)?(.*?)```"
        
    match = re.search(pattern, llm_output, re.DOTALL)
    if match:
        # If a markdown code block is found, return its content
        return match.group(1).strip()
    else:
        # If no markdown block is found, assume the whole output is code
        return llm_output.strip()
    
    # for chunk in client.models.generate_content_stream(
    #     model=model,
    #     contents=contents,
    #     config=generate_content_config,
    # ):
    #     print(chunk.text, end="")

# if __name__ == "__main__":
#     task = {
#     "task_id": 1,
#     "description": "Analyze the image 'sales_chart.png' to extract the sales data. Extract the sales amount and sales volume for each salesperson. Save the extracted data as a JSON file named 'task_1_extracted_data.json'.",
#     "tool_needed": "vision",
#     "dependencies": [],
#     "input_artifacts": [],
#     "output_artifacts": [
#       "task_1_extracted_data.json"
#     ]
#   }
#     print(visual_analysis("sales_chart.png", task))
