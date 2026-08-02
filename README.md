# DataScribe

**Multi-Agent AI Data Analysis Platform**

DataScribe is an autonomous, multi-agent data science assistant. Upload a dataset (CSV/Excel/Parquet), ask a question in plain English, and watch a team of specialized AI agents plan, generate code, execute it in a secure sandbox, critique the results, and produce a polished report with interactive charts — all streamed live to your browser.

---

## ✨ Highlights

- **8-agent LangGraph workflow** — Conversation → Initialize → Supervisor → Planner → Programmer → Executor → Critic → Reporter
- **Live SSE streaming** — Every agent step, code snippet, execution output, and report token streams in real time
- **Secure code execution** — Generated Python runs inside an isolated [E2B](https://e2b.dev) sandbox with AST-based guardrails
- **Interactive visualizations** — Plotly HTML charts and static PNG charts rendered inline with fullscreen & download support
- **Self-correcting loop** — The Critic agent reviews results and can request the Programmer to retry with feedback
- **Report export** — Download reports as PDF or self-contained interactive HTML
- **LangSmith integration** — Prompt management, tracing, and a full evaluation framework
- **Dark / light theme** with a gold-accented design system

---

## 🏗️ Architecture

![DataScribe](image.png)

### Agent Descriptions

| Agent | Role |
|---|---|
| **Conversation** | Classifies the user query — routes to the full analysis workflow, answers directly, or rejects |
| **Initialize** | Loads the uploaded dataset, extracts schema (dtypes, null counts, memory usage) |
| **Supervisor** | Decides the next high-level action: plan more analysis, generate a report, or end |
| **Planner** | Breaks the request into analysis, visualization, and statistical tasks with an execution order |
| **Programmer** | Generates Python code (pandas, matplotlib, seaborn, plotly) to fulfill the plan |
| **Executor** | Runs the code in an E2B sandbox, collects charts and output, downloads artifacts |
| **Critic** | Reviews execution results — passes, fails (triggers retry), or aborts |
| **Reporter** | Assembles the final markdown report with embedded charts and memory updates |

---

## LangGraph Workflow
![DataScribe](workflow_diagram.png)

## 🚀 Quick Start

### Prerequisites

- **Python 3.12**
- **Node.js 20+**
- A **Groq API key** ([groq.com](https://console.groq.com))
- An **E2B API key** ([e2b.dev](https://e2b.dev)) for sandbox code execution
- A **LangSmith API key** ([smith.langchain.com](https://smith.langchain.com)) for prompt management

### 1. Clone & Install

```bash
git clone https://github.com/Noore-hira/DataScribe.git
cd DataScribe
```

### 2. Backend

```bash
# Install Python dependencies
pip install -r requirements.txt

# Configure environment
cp Backend/app/src/evaluation/.env .env
# Edit .env with your Groq, E2B, and LangSmith API keys

# Run the API server
uvicorn Backend.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000` with auto-generated docs at `/docs`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

### 4. Docker (Alternative)

```bash
docker build -t datascribe .
docker run -p 8000:8000 --env-file .env datascribe
```

### 5. CI/CD Pipeline

DataScribe includes a GitHub Actions workflow (`.github/workflows/deploy.yml`) that automatically builds and deploys the Docker image on every push to `main`:

| Step | Description |
|---|---|
| **Trigger** | Runs on push to the `main` branch |
| **Build** | Builds the Docker image from the `Dockerfile` |
| **Push** | Pushes the image to **AWS ECR** (`us-east-1` region, repository: `datascribe-backend`) |
| **Secrets** | Requires `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` configured in GitHub repository secrets |

To set up the CI/CD pipeline, add the following secrets to your GitHub repository:

1. Go to **Settings → Secrets and variables → Actions**
2. Add `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` with permissions to push to ECR

---

## 📖 Usage

1. **Enter your Groq API key** in the Settings panel (stored locally in your browser only).
2. **Upload a dataset** — drag & drop or click the attachment button. Supports CSV, Excel, and Parquet (max 25 MB).
3. **Ask a question** in plain English, e.g.:
   - *"What's the average salary by department?"*
   - *"Create a bar chart of sales by region and a correlation heatmap."*
   - *"Run a t-test on the two groups and summarize the findings."*
4. **Watch the agents work** in real time via the Agent Monitor panel — see code generation, execution output, and chart previews as they happen.
5. **Review the report** in the Reports tab. Export as PDF or interactive HTML.

---

## 🔌 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/upload` | Upload a dataset (multipart form, max 25 MB) |
| `GET` | `/api/chat/stream` | SSE stream for agent workflow execution |
| `GET` | `/api/report/{filename}` | Download a generated report file |
| `DELETE` | `/api/session/{thread_id}` | Clear all files for a session |
| `GET` | `/storage/{path}` | Serve uploaded files |
| `GET` | `/charts/{path}` | Serve generated chart artifacts |

### Chat Stream Parameters

```
GET /api/chat/stream?message=What+is+the+trend&thread_id=abc-123&api_key=gsk_...&model=llama-3.3-70b-versatile&dataset_path=/path/to/data.csv
```

---

## 🧪 Evaluation

DataScribe includes a LangSmith-based evaluation framework for assessing individual agents:

```bash
# Evaluate the conversation router
python evaluation/evaluate_conversation.py

# Evaluate the planner
python evaluation/evaluate_planner.py

# Evaluate the programmer
python evaluation/evaluate_programmer.py
```

Evaluation datasets live in `evaluation/datasets/` and custom evaluators in `evaluation/evaluators/`.

---

## 📁 Project Structure

```
DataScribe/
├── Backend/
│   ├── main.py                          # FastAPI app entry point
│   ├── app/
│   │   ├── api/                         # REST + SSE endpoints
│   │   │   ├── chat.py                  # SSE streaming endpoint
│   │   │   ├── upload.py                # Dataset upload
│   │   │   ├── health.py                # Health check
│   │   │   ├── report.py                # Report download
│   │   │   └── session.py               # Session cleanup
│   │   ├── services/
│   │   │   ├── graph_service.py         # LangGraph execution runner
│   │   │   └── stream_service.py        # SSE event processing & heartbeat
│   │   └── src/
│   │       ├── config.py                # LLM factory (Groq, per-user key)
│   │       ├── data_frame.py            # Dataset loading (CSV/Excel/Parquet)
│   │       ├── agents/                  # 8 LangGraph agent nodes
│   │       │   ├── conversation_node.py
│   │       │   ├── initialize_node.py
│   │       │   ├── supervisor_node.py
│   │       │   ├── planner_node.py
│   │       │   ├── programmer_node.py
│   │       │   ├── executor_node.py
│   │       │   ├── critic_node.py
│   │       │   └── reporter_node.py
│   │       ├── graph/
│   │       │   ├── graph_workflow.py    # Workflow definition & routing
│   │       │   ├── state.py             # TypedDict state schema
│   │       │   └── state_utils.py       # State accessors
│   │       ├── memory/
│   │       │   └── memory_manager.py    # Session summary & compression
│   │       ├── utils/
│   │       │   ├── code_executor.py     # Code extraction & execution
│   │       │   └── safe_execution.py    # AST-based code guardrails
│   │       └── logs/
│   │           └── logger.py            # Structured logging
│   └── storage/                         # Uploaded datasets & reports
├── frontend/
│   ├── src/
│   │   ├── App.tsx                      # Root component (routes, providers)
│   │   ├── main.tsx                     # React entry point
│   │   ├── pages/                       # ChatPage, ReportsPage, SettingsPage
│   │   ├── components/
│   │   │   ├── layout/                  # Sidebar, Header, RightPanel
│   │   │   ├── chat/                    # ChatMessage, ChatInput
│   │   │   ├── upload/                  # UploadCard
│   │   │   ├── workflow/                # WorkflowEvents, AgentMonitor
│   │   │   ├── report/                  # ReportViewer
│   │   │   ├── agents/                  # AgentCard, AgentMonitor
│   │   │   ├── settings/                # ApiKeyInput, ModelSelector, ThemeToggle
│   │   │   └── common/                  # Logo, AnimatedBackground, StatusBadge
│   │   ├── contexts/                    # Settings, Session, Workflow contexts
│   │   ├── services/                    # api.ts, sse.ts
│   │   ├── hooks/                       # use-toast, use-connection-status
│   │   ├── types/                       # TypeScript type definitions
│   │   └── lib/                         # Utility functions
│   └── public/
├── evaluation/                          # LangSmith evaluation framework
│   ├── evaluate_conversation.py
│   ├── evaluate_planner.py
│   ├── evaluate_programmer.py
│   ├── judge.py
│   ├── upload_dataset.py
│   ├── evaluators/
│   └── datasets/
├── Dockerfile
├── langgraph.json
├── pyproject.toml
├── requirements.txt
└── workflow_diagram.png
```

---

## ⚙️ Configuration

### Environment Variables (`.env`)

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key (also provided per-request from the frontend) |
| `E2B_API_KEY` | E2B sandbox API key for code execution |
| `LANGSMITH_API_KEY` | LangSmith API key for prompt management & tracing |
| `LANGSMITH_PROJECT` | LangSmith project name (default: `DataScribe`) |
| `LANGGRAPH_ARTIFACTS_DIR` | Directory for chart artifacts (default: `/tmp/charts`) |

### Supported LLM Models

- `llama-3.3-70b-versatile` (default)
- `llama-3.1-8b-instant`
- `openai/gpt-oss-120b`

---

## 🛡️ Security

- **Per-user API keys** — The Groq API key is provided by the user at request time; no server-side key storage.
- **E2B sandbox** — All generated Python code executes in an isolated, ephemeral sandbox.
- **AST guardrails** — Generated code is validated before execution: dangerous builtins, filesystem APIs, and network calls are blocked.
- **CSP headers** — Strict Content-Security-Policy on API routes; relaxed CSP only for interactive chart iframes.
- **File upload limits** — 25 MB max, restricted to CSV/Excel/Parquet.

---

## 📜 License

Apache License 2.0 — see [LICENSE](LICENSE).

---

## 🙏 Acknowledgements

- **[LangGraph](https://langchain.com/langgraph)** — Multi-agent workflow orchestration
- **[LangChain](https://langchain.com)** — LLM abstractions and prompt management
- **[Groq](https://groq.com)** — Fast LLM inference
- **[E2B](https://e2b.dev)** — Secure cloud sandboxes for code execution
- **[LangSmith](https://smith.langchain.com)** — Prompt management, tracing, and evaluation
- **[Plotly](https://plotly.com)** & **[Seaborn](https://seaborn.pydata.org)** — Data visualization
- **[FastAPI](https://fastapi.tiangolo.com)** — Backend web framework
- **[React](https://react.dev)** + **[Vite](https://vitejs.dev)** + **[Tailwind CSS](https://tailwindcss.com)** — Frontend stack
