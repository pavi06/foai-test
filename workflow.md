
# fo.ai – Workflow & Architecture

This document outlines the system design, runtime workflow, and architecture decisions for `fo.ai`.

---

## 🧠 Core Components

| Layer      | Description |
|------------|-------------|
| `api.py`   | FastAPI entrypoint for LLM and cost logic |
| `foai_ui.py` | Streamlit UI – analyze vs. chat toggle |
| `foai_cli.py` | Local CLI with server management and logs |
| `rules/aws/` | Static cost optimization rules per service |
| `data/aws/` | EC2 fetchers (CloudWatch / Boto3) |
| `memory/` | Redis-backed memory + user context |
| `.env`     | Config for API URL and mock/live toggles |

---

## 🔁 Workflow (Streaming Query)

1. User submits question via UI or CLI
2. `FastAPI /analyze/stream` endpoint triggers:
   - Fetch EC2 data (live or mock)
   - Run through rule engine
   - Format natural language prompt
3. LangChain + Ollama streams response
4. Redis memory stores question & response (if enabled)
5. UI/CLI renders stream token-by-token

---

## 🧪 Development Tips

- Use `.env` to toggle between live and mock data
- Logs are saved in `logs/api.log` and `logs/ui.log`
- Run CLI tests with `test_foai_cli.sh`

---

## 🌱 Next Milestones

- Personalized Redis rules (Spike 1.2)
- LangGraph memory integration (Spike 3)
- Add support for S3, RDS, and multi-cloud

---

## 🔄 Git Flow

- Use `main` for stable
- Create branches: `feature/XX-description`
- Push, PR, and test

---

## 👥 Maintainers

- You (Vedanta) – Lead Architect
- ChatGPT (Co-Pilot 😉)
