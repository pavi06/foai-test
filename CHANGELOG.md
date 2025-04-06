## [v0.1.5] - 2025-04-06
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

