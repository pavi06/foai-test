#!/bin/bash

echo "🧪 Starting fo.ai CLI test suite..."

# Set colors for output
GREEN='\\033[0;32m'
RED='\\033[0;31m'
NC='\\033[0m' # No Color

run_test() {
  echo -n "🔹 $1... "
  eval "$2" &>/dev/null
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}PASSED${NC}"
  else
    echo -e "${RED}FAILED${NC}"
  fi
}

# Test status
run_test "API status check" "python foai_cli.py status"

# Test stream query
run_test "Ask (stream mode)" "python foai_cli.py ask 'Do I have idle EC2 instances?' --stream"

# Test ask (sync mode)
run_test "Ask (sync mode)" "python foai_cli.py ask 'Give me cost-saving opportunities in us-east-1'"

# Start servers
run_test "Start API server" "python foai_cli.py server start api && sleep 2"
run_test "Start UI server" "python foai_cli.py server start ui && sleep 2"

# Check logs exist
run_test "API log file exists" "[ -f logs/api.log ]"
run_test "UI log file exists" "[ -f logs/ui.log ]"

# Stop servers
run_test "Stop API server" "python foai_cli.py server stop api"
run_test "Stop UI server" "python foai_cli.py server stop ui"

# Force kill
run_test "Force kill (safe test)" "python foai_cli.py server forcekill all"

# Cleanup
rm -f .foai/*.pid &>/dev/null

echo "✅ All tests completed."
