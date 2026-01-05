# 🛡️ Sentinel

**AI-Powered Code Review Agent** — An autonomous bot that reviews GitHub Pull Requests against your team's Architectural Decision Records (ADRs).

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic_AI-purple)

---

## 🚀 Features

- **Agentic Workflow**: Multi-step LangGraph pipeline with conditional routing
- **RAG-Powered**: Retrieves relevant ADRs from Pinecone vector database
- **Tool-Calling**: Agent can fetch full file contents when diff context is insufficient
- **GitHub Integration**: Reads PR diffs, posts review comments, tracks conversations
- **Conversation Memory**: Responds to developer replies on previous reviews

---

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Analyze    │────▶│  Retrieve   │────▶│   Review    │
│    Diff     │     │    ADRs     │     │   Agent     │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                    ┌──────────┴──────────┐
                                    ▼                     ▼
                              ┌──────────┐         ┌──────────┐
                              │  Tools   │◀───────▶│  Filter  │
                              │ Executor │         │  Agent   │
                              └──────────┘         └────┬─────┘
                                                        │
                                                        ▼
                                                  ┌──────────┐
                                                  │ Publish  │
                                                  │ Comment  │
                                                  └──────────┘
```

---

## 📁 Project Structure

```
├── app.py                 # FastAPI server & webhook endpoint
├── seed_adrs.py           # Script to upload ADRs to Pinecone
├── Dockerfile             # Container configuration
├── requirements.txt       # Python dependencies
├── adrs/                  # Architectural Decision Records
│   ├── ADR-001-No-Direct-SQL.md
│   └── ADR-002-Use-V2-Logger.md
└── src/
    ├── config.py          # Environment configuration
    ├── github_client.py   # GitHub API wrapper
    ├── graph.py           # LangGraph workflow definition
    ├── nodes.py           # Agent nodes & tools
    ├── rag.py             # Pinecone retriever
    ├── runner.py          # Core review orchestrator
    └── state.py           # Typed state schema
```

---

## ⚙️ Setup

### 1. Clone & Install

```bash
git clone https://github.com/Durvankur-Rasal/shadow-backend-final.git
cd shadow-backend-final
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file:

```env
GITHUB_TOKEN=ghp_your_token_here
GROQ_API_KEY=your_groq_api_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=sentinel-adrs
API_SECRET=your_webhook_secret
DRY_RUN=true
```

### 3. Seed the Vector Database

```bash
python seed_adrs.py
```

### 4. Run the Server

```bash
uvicorn app:app --reload
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/`      | Health check |
| `POST` | `/review`| Trigger PR review |

### Trigger a Review

```bash
curl -X POST http://localhost:8000/review \
  -H "Content-Type: application/json" \
  -d '{
    "repo_name": "owner/repo",
    "pr_number": 42,
    "secret_token": "your_webhook_secret"
  }'
```

---

## 🐳 Docker Deployment

```bash
docker build -t sentinel .
docker run -p 8000:8000 --env-file .env sentinel
```

---

## 🧠 Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | FastAPI |
| AI Orchestration | LangGraph |
| LLM | Groq (Llama 3.3 70B) |
| Vector DB | Pinecone |
| Embeddings | HuggingFace (all-mpnet-base-v2) |
| GitHub | PyGithub |

---

## 📝 Adding Custom ADRs

1. Create a new `.md` file in the `adrs/` folder
2. Follow this format:
   ```markdown
   # ADR-XXX: Title
   
   ## Context
   Why this decision matters...
   
   ## Decision
   What we decided to enforce...
   
   ## Consequences
   What happens if violated...
   ```
3. Re-run `python seed_adrs.py` to update the vector database

---

## 📄 License

MIT License — feel free to use and modify.

---

## 🤝 Contributing

Pull requests welcome! Please ensure your code follows the existing ADRs. 😉