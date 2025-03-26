# fo.ai – FinOps AI

A modular, LangGraph-powered AI assistant that helps identify AWS cost savings using mocked or real cloud data.

---

## 🚀 How to Run

### 1. Set up the environment
```bash
conda activate foai-env
pip install -r requirements.txt
```

### 2. Start the backend API
```bash
uvicorn api:app --reload
```

### 3. Start the Streamlit frontend
```bash
streamlit run streamlit_app.py
```

### 4. Use the CLI tool (optional)
```bash
python main.py
```

---

## ⚙️ Configuration via `.env`

```env
FOAI_WEB_URL=http://localhost:8501/
FOAI_API_URL=http://localhost:8000/analyze
USE_MOCK_DATA=True
DEBUG=True
```

---

## 📬 API Endpoint
### `POST /analyze`
#### Input:
```json
{
  "query": "Where can I save AWS costs?"
}
```
#### Output:
```json
{
  "response": "Here's a summary of the cost optimization recommendations..."
}
```

Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Mock Data Location
- `data/ec2_instances.json`
- `data/cost_explorer.json`
- `data/trusted_advisor.json`

---

## 📁 Directory Structure

```
fo.ai/
├── app/                # LangGraph logic and nodes
├── data/               # Mock data files
├── tests/              # Unit tests
├── main.py             # CLI entry point
├── api.py              # FastAPI backend
├── streamlit_app.py    # Streamlit frontend
├── requirements.txt
├── .env
└── README.md
```

---

## 📚 See Also
- `features.md`: Feature tracker
- `workflow.md`: Full architectural flow & LangGraph design