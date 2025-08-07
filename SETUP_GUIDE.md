# Getting Started with fo.ai

## What You're Getting Into

So you want to stop your AWS bill from giving you heart palpitations? Good choice! This guide will walk you through setting up fo.ai so you can finally understand what's actually costing you money.

We've made this as painless as possible, but you'll need a few things installed first. Don't worry - we'll walk through each step.

## What You'll Need

Before we dive in, make sure you have:

- **Python 3.8 or newer** (if you don't have it, grab it from python.org)
- **Redis** (for storing your preferences and chat history)
- **AWS access** (your credentials should be set up)
- **Ollama** (for running the AI models locally)

Don't panic if you don't have these yet - we'll get them set up together.

## Step 1: Get the Code

First, let's grab the fo.ai code:

```bash
git clone <repository-url>
cd fo.ai
```

## Step 2: Install the Dependencies

This is the easy part - just run:

```bash
pip install -r requirements.txt
```

Go grab a coffee while this runs. It might take a few minutes the first time.

## Step 3: Set Up Your Environment

Create a file called `.env` in the fo.ai folder. This is where you'll put your configuration:

```env
# Basic settings
FOAI_API_URL=http://localhost:8000
USERNAME=your_name_here
AWS_REGION=us-east-1

# AI settings
LLM_MODEL=llama3
LLM_TEMPERATURE=0.5

# Redis (usually this works out of the box)
REDIS_URL=redis://localhost:6379

# AWS credentials (if you haven't set them up with AWS CLI)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
```

**Pro tip**: If you've already set up AWS CLI with `aws configure`, you can skip the AWS credentials part.

## Step 4: Get Redis Running

Redis is what we use to remember your preferences and chat history. Here's how to start it:

**On Mac (with Homebrew):**
```bash
brew services start redis
```

**On Ubuntu/Debian:**
```bash
sudo systemctl start redis-server
```

**On Windows:** 
Download Redis from the official site or use WSL.

**Want to test if it's working?**
```bash
redis-cli ping
```
If it says "PONG", you're good to go!

## Step 5: Set Up Ollama (The AI Part)

Ollama is what runs the AI models locally. Here's how to get it:

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the Llama3 model (this might take a while)
ollama pull llama3

# Start the Ollama service
ollama serve
```

The model download might take a few minutes depending on your internet speed. Perfect time for another coffee!

## Step 6: Fire It Up

Now for the fun part! You have two options:

### Option A: The Easy Way (Recommended)
```bash
python foai_cli.py server start all
```

This starts both the API and the web interface. Then just open your browser to http://localhost:8501

### Option B: The Manual Way
If you want to see what's happening under the hood:

```bash
# Terminal 1 - Start the API
uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Start the web interface
streamlit run foai_ui.py
```

## Making It Your Own

### Setting Up Your Preferences

Once you have the web interface open, you'll see a sidebar with settings. Here's what each section does:

**EC2 Preferences:**
- **CPU Threshold**: How low does CPU usage need to be before we flag an instance? (Default: 10%)
- **Min Uptime**: How long should an instance be running before we suggest stopping it? (Default: 24 hours)
- **Min Savings**: What's the minimum amount we should save before recommending changes? (Default: $5)
- **Excluded Tags**: Any instances with these tags will be ignored (useful for production systems)

**S3 Preferences:**
- **Transition Days**: When should we move objects to cheaper storage? (30 days for IA, 90 for Glacier, etc.)
- **Analysis Settings**: What should we check? (Versioning, logging, encryption)

### Asking Questions

The fun part! You can ask questions in plain English. Here are some examples to get you started:

**For EC2:**
- "Which instances are wasting money?"
- "Find underutilized EC2 instances"
- "Analyze instance i-1234567890abcdef0"
- "Show me expensive instances that could be optimized"

**For S3:**
- "Which buckets need lifecycle policies?"
- "Analyze my S3 buckets for cost optimization"
- "Check bucket 'my-app-logs' for optimization"

**General:**
- "What are my biggest cost optimization opportunities?"
- "How can I reduce my AWS costs?"
- "Give me a comprehensive cost analysis"

## Understanding What You Get Back

When you ask a question, fo.ai will give you:

1. **A conversational summary** - What it found in plain English
2. **Specific recommendations** - Exactly which resources need attention
3. **Real numbers** - How much money you could save
4. **Actionable steps** - What to do about it

For example, instead of "CPU utilization is low", you'll get "Instance i-abc123 is running at 5% CPU but costing $45/month. You could save $36/month by stopping it during non-business hours."

## Troubleshooting (When Things Go Wrong)

### "Redis connection failed"
- Make sure Redis is running: `brew services start redis` (Mac) or `sudo systemctl start redis-server` (Linux)
- Check if you can connect: `redis-cli ping`

### "AWS credentials not found"
- Run `aws configure` to set up your credentials
- Or add them to your `.env` file
- Make sure you have the right permissions

### "Ollama model not found"
- Make sure Ollama is running: `ollama serve`
- Check if the model is installed: `ollama list`
- If not, install it: `ollama pull llama3`

### "No analysis results"
- Check your AWS region (make sure it matches where your resources are)
- Verify your AWS credentials have the right permissions
- Try adjusting your preference thresholds (maybe they're too strict)

### "The web interface won't load"
- Check if the API is running on port 8000
- Check if Streamlit is running on port 8501
- Look at the terminal output for error messages

## Getting Help

Stuck? Here are some things to try:

1. **Check the logs**: `python foai_cli.py logs api` or `python foai_cli.py logs ui`
2. **Enable debug mode**: Add `DEBUG=True` to your `.env` file
3. **Ask the community**: Open an issue on GitHub
4. **Check the API docs**: Visit http://localhost:8000/docs when the API is running

## What's Next?

Once you have everything running, you can:

- **Explore the API**: Visit http://localhost:8000/docs to see all the endpoints
- **Try the CLI**: Use `python foai_cli.py --help` to see all the commands
- **Customize your rules**: Modify the preference thresholds to match your needs
- **Set up alerts**: Use the API to integrate with your monitoring tools

## Pro Tips

- **Start with mock data**: Set `USE_MOCK_DATA=true` in your `.env` to test without hitting AWS
- **Use specific queries**: Instead of "analyze everything", try "analyze instance i-abc123"
- **Save your preferences**: The system remembers your settings, so you don't have to reconfigure every time
- **Check the chat history**: Your previous analyses are saved and can be reviewed

## Contributing

Found a bug? Have an idea for a feature? Want to help make this better?

1. Fork the repository
2. Create a branch for your changes
3. Make your changes (and add tests if you can)
4. Send us a pull request

We love contributions, big and small!

---

*Happy cost optimizing! 🎉*

Remember: The goal is to save money, not to break anything. Always test changes in a non-production environment first! 