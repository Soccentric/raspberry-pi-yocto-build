#!/bin/bash
set -e

# Default port for Streamlit
PORT=8501

# Parse command line arguments
while getopts ":p:" opt; do
  case $opt in
    p)
      PORT=$OPTARG
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
  esac
done

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "⚠️ Virtual environment not found. Running setup first..."
    ./setup.sh
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "🔧 Activating virtual environment..."
    source .venv/bin/activate
fi

# Run Streamlit app
echo "🚀 Starting Embedded Linux Builder on port $PORT..."
streamlit run app.py --server.port $PORT 