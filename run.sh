#!/bin/bash
# Load env vars from .env file
set -a
source "$(dirname "$0")/.env"
set +a

# Run the Python script
python3 "$(dirname "$0")/send.py"
