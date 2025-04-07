
# fo.ai – Changelog

---

## [v0.1.6] – 2025-04-06  
### 🔁 Spike 2 – Streaming Chat Output (CLI)

This release introduces a real-time, context-aware chat interface to the CLI. It enables streaming LLM responses using live or mock EC2 data and personalized user preferences.

### ✨ Features
- **New `chat` CLI command**
  - Interactive prompt powered by `/analyze/stream`
  - Streams LLM responses token-by-token
  - Loads and injects EC2 instance data from `/analyze`
  - Builds custom prompt using instance IDs, CPU stats, and savings
- **Preference-aware streaming**
  - Loads user preferences via `/preferences/load`
  - Filters EC2 recommendations accordingly
- **Safe field access**
  - Handles missing data (`AvailabilityZone`, `AverageCPU`, etc.) gracefully
- **Preserves `ask` command stability**
  - `chat` implemented as a modular plugin (`cli_chat.py`)

### 🧪 Improvements
- Improved prompt quality and context grounding
- Accurate reasoning about EC2 optimization in real time
- Smarter CLI experience without backend refactors

### ✅ Merged
- `spike-2-chat` → `main`

### 🏷️ Tag
- `v0.1.6`

---

## [v0.1.5] – 2025-04-06  
### 🔧 Spike 1.2 – Preference Memory (UI + CLI + API)

This release completes Spike 1.2 by introducing full user preference support across the fo.ai system.

#### ✨ Features
- **Redis-backed user preferences**
  - `cpu_threshold`, `min_uptime_hours`, `min_savings_usd`, `excluded_tags`, `idle_7day_cpu_threshold`
- **Streamlit UI Enhancements**
  - Preferences panel with `st.expander` groups
  - Auto-load on startup
  - Save-on-submit with toast notifications
  - Detailed optimization output per resource
- **CLI Enhancements**
  - View and set preferences from terminal
  - Flags: `--cpu-threshold`, `--uptime`, `--min-savings`, `--exclude-tags`, `--idle-cpu`
- **FastAPI Endpoints**
  - `POST /preferences/save`
  - `GET /preferences/load`
  - `POST /preferences/reset`
  - Preferences injected into `/analyze` and `/analyze/stream`

#### ✅ Merged
- `spike-1.2-prefs` → `main`

#### 🏷️ Tag
- `v0.1.5`
