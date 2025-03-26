# fo.ai – Internal Workflow Overview

This document describes how fo.ai works under the hood and how to transfer the project context to a new developer or chat session.

Prompt : "I'm working on a project called fo.ai – here's workflow.md and features.md. Let's continue."

---

## 🔄 High-Level Workflow

```
User Query
   ↓
analyze_query → fetch_mock_data → generate_recommendations → generate_response
```

Powered by **LangGraph’s StateGraph**, each node takes in a shared `CostState`, updates it, and passes it along.

---

## 🧠 LangGraph Nodes

### `analyze_query`
- Uses `ChatOllama` (Llama 3) to classify the query
- Sets `query_type`: `ec2`, `service`, `region`, or `general`

### `fetch_mock_data`
- Loads data from `data/*.json`
- Honors `use_mock` flag
- Will later call real AWS APIs if `use_mock=False`

### `generate_recommendations`
- Rule-based recommendations
  - EC2 underutilization (CPU < 10%)
  - Cost thresholds (>$100)
  - Trusted Advisor checks

### `generate_response`
- Uses LLM to summarize recommendations into Markdown/HTML

---

## 🧾 CostState (Shared LangGraph State)
```python
class CostState(TypedDict, total=False):
    query: str
    query_type: Literal["general", "ec2", "region", "service"]
    ec2_data: list
    cost_data: dict
    recommendations: list
    response: str
    use_mock: bool
    debug: bool
```

---

## ⚙️ Configuration via `.env`
- All key runtime flags are read from `.env`
  - `USE_MOCK_DATA`
  - `DEBUG`
- Flags are passed into LangGraph state (`state['use_mock']`, `state['debug']`)

---

## 🧠 LLM Usage Summary
- LLM is used in two places:
  1. `analyze_query` (to classify the question)
  2. `generate_response` (to summarize recs in plain English)

---

## 🔁 Switching Chats / Sessions

If this chat becomes too long or slow:
- Open a **new ChatGPT thread**
- Copy-paste this `workflow.md` and `features.md`
- Say: `I was working on a project called fo.ai – here's the architecture + feature set. Let's continue.`

---

## 🧱 How to Extend
- Add new node functions in `app/nodes/`
- Update `app/graph.py` with new LangGraph edges
- Add tests under `/tests`
- Add new query types and routing logic in `analyze_query`
- Swap in real AWS APIs via `boto3` when `use_mock=False`

---

_Last updated after MVP v0.1.0 merge to main_ ✅

