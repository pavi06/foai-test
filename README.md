
# fo.ai – Your Cloud Cost Companion

**Version:** `v0.1.3`  
**Built by:** A team that got tired of surprise AWS bills

---

## What's This All About?

Hey there! 👋 We built `fo.ai` because we were spending way too much time staring at AWS bills and wondering where all our money went. You know that feeling when you get that monthly invoice and think "wait, what's this $200 charge for?" Yeah, we've been there too.

`fo.ai` is our attempt to make cloud cost optimization less painful. It's like having a smart friend who actually understands AWS pricing and can tell you exactly which instances are just sitting there burning money.

---

## What Can It Do For You?

Here's what we've packed into this thing:

- **🔍 Smart EC2 Analysis**: Finds those sneaky underutilized instances that are costing you money
- **🧠 AI-Powered Insights**: Uses LLMs to explain what's happening in plain English
- **⚡ Real-time Streaming**: Get answers as they're being generated (no more waiting!)
- **🎯 Targeted Analysis**: Want to check just one specific instance? No problem
- **💾 Memory**: Remembers your preferences and past analyses
- **🎨 Clean UI**: Both web interface and command line - use whatever you prefer
- **📊 Detailed Reports**: Not just "save money" - actual numbers and specific actions

---

## Getting Started (The Quick Way)

### 1. Grab the Code

```bash
git clone https://github.com/your-org/fo.ai.git
cd fo.ai
pip install -r requirements.txt
```

### 2. Set Up Your Environment

Create a `.env` file with:

```env
FOAI_API_URL=http://localhost:8000
USE_MOCK_DATA=false  # Set to false when you want real AWS data
```

### 3. Fire It Up

```bash
python foai_cli.py server start all
```

Then open your browser to [http://localhost:8501](http://localhost:8501) and start asking questions!

---

## How to Use It

### The Easy Way (Web Interface)

Just type questions like:
- "Which EC2 instances are wasting money?"
- "Analyze instance i-1234567890abcdef0"
- "Check my S3 bucket 'my-app-logs' for optimization"

### The Power User Way (Command Line)

```bash
# Ask a quick question
python foai_cli.py ask "How can I save money on EC2?"

# Get streaming responses (more fun to watch)
python foai_cli.py ask "Show me underutilized instances" --stream

# Check if everything is running
python foai_cli.py status

# Start/stop the servers
python foai_cli.py server start all
python foai_cli.py server stop all
```

### Pro Tip: Make It Global

Add this to your shell config (`~/.zshrc` or `~/.bashrc`):

```bash
alias foai="python /full/path/to/foai_cli.py"
```

Then you can just type:
```bash
foai ask "What's costing me money?"
foai server start all
```

---

## What Makes This Different?

We've been using various cloud cost tools, and honestly, most of them either:
- Give you generic advice that doesn't help
- Dump a ton of data without explaining what to do
- Cost more than they save

So we built something that:
- **Actually explains things** - No more "CPU utilization is low" without context
- **Gives specific actions** - "Stop instance i-abc123 during non-business hours" instead of "optimize"
- **Shows real numbers** - "You'll save $45/month" instead of "potential savings"
- **Works with your workflow** - CLI, web UI, or API - whatever you prefer

---

## Under the Hood

If you're curious about how it works:

- **Backend**: FastAPI (because it's fast and we're impatient)
- **Frontend**: Streamlit (because we wanted something that just works)
- **AI**: LangChain + Ollama (open source LLMs, no vendor lock-in)
- **Memory**: Redis (because we want it to remember your preferences)
- **Data**: AWS CloudWatch + boto3 (the official AWS SDK)

---

## What We're Working On

We're not done yet! Here's what's coming:

- [x] **EC2 Analysis** - Find those money-wasting instances
- [x] **S3 Optimization** - Lifecycle policies and storage class recommendations
- [x] **Single Resource Analysis** - Check specific instances or buckets
- [ ] **Multi-cloud Support** - Because not everyone is all-in on AWS
- [ ] **Slack Integration** - Get alerts when you're burning money
- [ ] **Custom Rules Engine** - Set your own optimization criteria
- [ ] **Cost Forecasting** - Predict what your bill will be next month

---

## Contributing

Found a bug? Have an idea? Want to help? We'd love to hear from you!

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Test them (we have a test suite, promise!)
5. Send us a pull request

Or just open an issue and tell us what's on your mind.

---

## The Tech Stack

We're using some pretty cool open source tools:

- **[LangChain](https://github.com/langchain-ai/langchain)** - For all the AI magic
- **[FastAPI](https://fastapi.tiangolo.com/)** - Because we like fast APIs
- **[Streamlit](https://streamlit.io/)** - For the web interface
- **[Redis](https://redis.io/)** - For remembering stuff
- **[Ollama](https://ollama.com/)** - For running LLMs locally

---

## License

MIT License - Use it, modify it, make it better. Just don't blame us if your AWS bill goes up! 😄

---

## Support

Having trouble? Here are some things to check:

1. **Make sure Redis is running**: `brew services start redis` (on Mac)
2. **Check your AWS credentials**: Make sure you have access to the resources you're trying to analyze
3. **Look at the logs**: `python foai_cli.py logs api` or `python foai_cli.py logs ui`

Still stuck? Open an issue and we'll help you out!

---

*Built with ♥ by people who got tired of surprise cloud bills*
