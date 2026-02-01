#!/bin/sh
set -e

# Optional: run database init if needed. Uncomment if you want automatic DB init
# python scripts/init_db.py

# Start FastAPI (Uvicorn) and Streamlit. Both run in background and we wait.
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Start Streamlit in headless mode
streamlit run ui/app.py --server.port 8501 --server.headless true &

# Wait for any process to exit
wait
