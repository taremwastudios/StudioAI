#!/bin/bash
# Taremwa Studios - Autonomous Lab Startup
# This script ensures the Learner starts only when internet is active.

cd /home/Taremwastudios/TaremwaStudios/gemi-engine-app

# Wait for internet connection (max 60 seconds)
MAX_RETRIES=12
COUNT=0
while ! ping -c 1 google.com > /dev/null 2>&1; do
    if [ $COUNT -ge $MAX_RETRIES ]; then
        echo "No internet. Lab starting in Offline Mode (Indexing Only)."
        break
    fi
    sleep 5
    COUNT=$((COUNT+1))
done

# Run the learner in the background using the project venv
./venv/bin/python3 autonomous_learner.py >> lab.log 2>&1 &
echo "Matrix Lab initialized. Learning in background."
