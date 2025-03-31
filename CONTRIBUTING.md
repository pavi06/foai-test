
# Contributing to fo.ai

We welcome contributions! Whether you're fixing bugs, adding features, or improving documentation, you're helping us make cloud cost intelligence more accessible.

---

## 🧭 Getting Started

1. Fork the repository
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/fo.ai.git
   cd fo.ai
   ```

3. Setup your environment:
   ```bash
   conda create -n foai-env python=3.10
   conda activate foai-env
   pip install -r requirements.txt
   ```

---

## 🛠️ Development Flow

We use [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/). Follow this convention:

- Base: `main`
- Feature branches: `feature/<spike-or-layer>-<name>`
- Hotfixes: `hotfix/<description>`

### Example:
```bash
git checkout -b feature/01-streaming-api
```

---

## 📦 Code Style

- Use **black** + **ruff** for formatting
- Keep code modular (`data/aws`, `rules/aws`, `memory/`)
- Follow LangChain + FastAPI best practices

---

## ✅ Submitting a PR

1. Commit with a clear message:
   ```bash
   git commit -m "✨ Add EC2 idle detection rule"
   ```

2. Push and open a PR to `main`:
   ```bash
   git push origin feature/01-ec2-idle
   ```

3. Fill in the PR template and wait for review

---

## 📃 License

By contributing, you agree that your work will be licensed under the MIT License.
