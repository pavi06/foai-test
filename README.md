
# fo.ai – Cloud Cost Intelligence

**Version:** `v0.1.3`  
**Tagline:** Your smart assistant for optimizing cloud costs, starting with AWS EC2.

---

## 🧭 Overview

`fo.ai` is a lightweight, intelligent tool for identifying cost-saving opportunities in your AWS environment. Backed by LLMs, rule engines, Redis memory, and a clean UI, it supports both one-shot queries and streaming AI responses.

---

## 🚀 Features

- ✅ EC2 instance cost analysis using CloudWatch metrics
- ✅ Static rules engine with customizable logic
- ✅ Redis-backed memory (for future personalization)
- ✅ LLM-powered summaries (streamed or static)
- ✅ FastAPI backend for APIs
- ✅ Streamlit web UI with toggle modes
- ✅ CLI tool for local interaction
- ✅ Logging, live tailing, and process control

---

## 🛠️ Setup Instructions

### 1. Clone the repo and install requirements

```bash
git clone https://github.com/your-org/fo.ai.git
cd fo.ai
conda activate foai-env  # or your preferred virtualenv
pip install -r requirements.txt
```

### 2. Setup `.env`

```env
FOAI_API_URL=http://localhost:8000
USE_MOCK_DATA=true
```

---

## 🧪 Running Locally

### Option 1: Full app (API + UI)

```bash
python foai_cli.py server start all
```

Then open: [http://localhost:8501](http://localhost:8501)

---

## 🧰 CLI Usage

```bash
python foai_cli.py --help
```

### 🧠 Ask a cost question

```bash
python foai_cli.py ask "How can I optimize EC2 usage in us-west-1?"
```

### 🔄 Stream LLM output

```bash
python foai_cli.py ask "Are there underutilized EC2s?" --stream
```

### 📡 Check API status

```bash
python foai_cli.py status
```

### ☁️ Manage Servers

```bash
python foai_cli.py server start all
python foai_cli.py server stop all
python foai_cli.py server forcekill all
```

### 📜 View Logs

```bash
python foai_cli.py logs api
python foai_cli.py logs ui
```

---

## ⚡ Setup CLI Alias (Optional)

To use `foai` as a global command:

```bash
echo 'alias foai="python /full/path/to/foai_cli.py"' >> ~/.zshrc  # or ~/.bashrc
source ~/.zshrc  # or source ~/.bashrc
```

Then use like:

```bash
foai ask "How do I save on EC2?"
foai server start all
```

---

## 🧪 Development Workflow

- Main API: [`api.py`](./api.py)
- CLI Tool: [`foai_cli.py`](./foai_cli.py)
- Web UI: [`foai_ui.py`](./foai_ui.py)
- Rule Engine: [`rules/aws/ec2_rules.py`](./rules/aws/ec2_rules.py)
- Redis Memory: [`memory/`](./memory/)
- Logs: `logs/api.log`, `logs/ui.log`

---

## 🧭 Roadmap

- [x] EC2 Analyzer (mock + live)
- [x] Streaming LLM responses
- [x] CLI support + logging
- [ ] Personalized rules via Redis (Spike 1.2)
- [ ] LangGraph memory node (Spike 3)
- [ ] S3 and other service optimizations
- [ ] Slack/Teams integrations

---

## 🧠 Powered By

- [LangChain](https://github.com/langchain-ai/langchain)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Streamlit](https://streamlit.io/)
- [Redis](https://redis.io/)
- [Open Source LLMs via Ollama](https://ollama.com/)

---

## 👥 License & Credits

MIT License – Built with ♥ by cloud cost nerds.
