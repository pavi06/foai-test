
## [v0.1.3] – 2025-03-31

### Added
- ✅ CLI streaming output with `--stream` flag
- ☠️ `forcekill` command to terminate orphaned API/UI processes
- 📜 Log redirection to `logs/api.log` and `logs/ui.log`
- 📡 `foai logs <api|ui>` to tail logs via CLI
- 🧾 Streamlit UI: Markdown buffering + "Thinking..." state
- 🎨 Chat mode ON by default, theme cleanup, sidebar toggles
- 🧰 CLI Help text for all commands (`--help`)
- 📄 User-facing `README.md`, `CONTRIBUTING.md`, and `WORKFLOW.md`

### Fixed
- 🐛 Streamed token rendering glitches in chat
- 📁 PID file issues with `.foai/` cleanup
- 📤 API and UI logs now rotate properly on restart
