#!/bin/bash
set -e

echo "🚀 Setting up the Embedded Linux Builder environment..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found. Please install Python 3 and try again."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not found. Please install pip3 and try again."
    exit 1
fi

# Check for essential dependencies
echo "🔍 Checking for essential dependencies..."
MISSING_DEPS=()

for cmd in git make docker; do
    if ! command -v $cmd &> /dev/null; then
        MISSING_DEPS+=($cmd)
    fi
done

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo "⚠️ Some recommended dependencies are missing: ${MISSING_DEPS[*]}"
    echo "  These may be required for full functionality."
    echo "  On Ubuntu/Debian, you can install them with:"
    echo "  sudo apt-get update && sudo apt-get install -y ${MISSING_DEPS[*]}"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 1
    fi
fi

# Check if KAS is installed
if ! command -v kas &> /dev/null; then
    echo "⚠️ KAS is not installed globally. It will be installed in the virtual environment."
fi

# Create and activate virtual environment
echo "🔧 Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install requirements
echo "📦 Installing required Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories if they don't exist
mkdir -p build

echo "✅ Setup complete! You can now run the application with:"
echo "  ./run.sh"
echo ""
echo "📘 For more information, check the README.md file."