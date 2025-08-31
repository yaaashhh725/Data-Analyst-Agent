# Data Analyst Agent

A modular, AI-powered workflow engine for automated data analysis, code generation, debugging, and vision tasks. This project orchestrates LLM agents to break down complex analytical requests, generate and execute code, analyze images, and debug failures—all in a stateless, file-driven pipeline within 3 minutes.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Setup & Running](#setup--running)
- [Frontend](#frontend)
- [API Endpoints](#api-endpoints)
- [Contributing](#contributing)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Features

- **Task Planning:** Breaks down user questions into granular, executable steps using LLMs.
- **Code Generation:** Generates Python scripts for each step, with context-aware logic.
- **Vision Agent:** Analyzes images and extracts structured data via LLM.
- **Automated Debugging:** Detects and fixes code errors using a dedicated debugging agent.
- **File-based State:** All intermediate results are saved as artifacts for stateless execution.
- **Extensible:** Easily add new agent types or tools.
- **Minimalistic Frontend:** Upload files and interact with the workflow via a simple web UI.

---

## Architecture

```
User Request (via Frontend or API)
    │
    ▼
Main Agent (task_breakdown)
    │
    ▼
Task Plan (JSON)
    │
    ▼
Task Orchestrator
    ├─► Code Generator Agent (Python tasks)
    │      └─► Executes code, saves output
    ├─► Vision Agent (Image tasks)
    │      └─► Analyzes images, saves JSON output
    └─► Debugger Agent (on failure)
           └─► Fixes code, retries execution
    │
    ▼
Final Output (final_output.json)
```

- **Agents:** Each agent is a Python module (see `api/`) with a clear role.
- **Artifacts:** All data is passed between tasks as files (Parquet, JSON, images).
- **Orchestration:** The orchestrator manages execution, retries, and error handling.

---

## Setup & Running

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/data_analyst_agent.git
cd data_analyst_agent
```

### 2. Install Dependencies

Create a virtual environment and install required packages:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

Create a `.env` file in the `api/` directory with your Gemini API key:

```
GEMINI_API_KEY=your_google_genai_api_key
```

### 4. Run Locally

Start the FastAPI server:

```bash
cd api
uvicorn main:app --reload
```

Visit [http://localhost:8000](http://localhost:8000) to access the API.

### 5. Use the Frontend

A minimalistic frontend is provided in `frontend/index.html`.  
You can open this file directly in your browser or serve it using any static file server.

**How to use:**
- Paste your questions in the textarea or upload a file named `questions.txt`.
- Optionally, upload additional data files (e.g., images, CSVs).
- Click "Upload" to send your files to the `/upload` endpoint.
- The result will be displayed below the form.

---

## Frontend

The frontend allows you to interact with the `/upload` endpoint and upload files required for analysis.

### **Expected Structure for `questions.txt`**

Your `questions.txt` should clearly describe the analytical task and the questions to be answered.  
**Example:**

```
Scrape the list of highest grossing films from Wikipedia. It is at the URL:
https://en.wikipedia.org/wiki/List_of_highest-grossing_films

Answer the following questions and respond with a JSON array of strings containing the answer.

1. How many $2 bn movies were released before 2000?
2. Which is the earliest film that grossed over $1.5 bn?
3. What's the correlation between the Rank and Peak?
4. Draw a scatterplot of Rank and Peak along with a dotted red regression line through it.
   Return as a base-64 encoded data URI, `"data:image/png;base64,iVBORw0KG..."` under 100,000 bytes.
```

- **`questions.txt` is mandatory.**
- You may upload additional files (images, CSVs, etc.) as needed for your analysis.

---

## API Endpoints

- `POST /upload`  
  Upload `questions.txt` and supporting files/images. Triggers the full workflow.

- `GET /final-result`  
  Retrieve the final output JSON after workflow completion.

- `GET /debug`  
  Inspect server environment and workspace files.

- `GET /task-breakdown`  
  Generate a task plan for a sample question.

- `GET /run-script`  
  Run a test script (for debugging).

---

## Contributing

We welcome contributions!

1. **Fork the repository** and create your branch.
2. **Write clear, modular code**—each agent should be a separate module.
3. **Add tests** for new features.
4. **Document your changes** in the README or code comments.
5. **Submit a pull request** with a detailed description.

**Code Style:**  
- Use Python 3.10+  
- Follow PEP8  
- Add docstrings for all functions/classes

---

## Environment Variables

- `GEMINI_API_KEY` – Required for all LLM agents (Google Generative AI).

---

## Troubleshooting

- **Serverless Limits:** On Vercel, keep dependencies minimal to avoid the 250MB unzipped size limit.
- **File Writes:** All temporary files must be written to `/tmp` on Vercel.
- **Missing API Key:** Ensure `GEMINI_API_KEY` is set in your environment.
- **Dependency Issues:** Runtime pip installs may fail on serverless platforms; pre-bundle as much as possible.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Acknowledgements

- [Google Generative AI](https://ai.google.dev/)
- [FastAPI](https://fastapi.tiangolo.com/)