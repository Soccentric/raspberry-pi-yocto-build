#!/bin/bash

echo "🚀 Jetson Build Manager Launcher"
echo "================================="

# Parse command-line options - now with defaults reversed
ENABLE_FLASH=true
DISABLE_FILE_WATCHING=true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --disable-flash)
      ENABLE_FLASH=false
      shift
      ;;
    --enable-file-watching)
      DISABLE_FILE_WATCHING=false
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --disable-flash          Disable flash functionality (enabled by default)"
      echo "  --enable-file-watching   Enable file watching (disabled by default)"
      echo "  --help, -h               Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for available options"
      exit 1
      ;;
  esac
done

# Check if the increase_inotify_limit.sh exists and is executable
if [ -f "increase_inotify_limit.sh" ]; then
    echo "🔍 Checking inotify watch limits..."
    CURRENT_LIMIT=$(cat /proc/sys/fs/inotify/max_user_watches)
    
    if [ "$CURRENT_LIMIT" -lt 8192 ]; then
        echo "⚠️  Current inotify watch limit is low: $CURRENT_LIMIT"
        echo "Would you like to increase it now? (y/n)"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            echo "Running increase_inotify_limit.sh..."
            sudo bash ./increase_inotify_limit.sh
        else
            echo "Continuing with current limit. The application may crash if it runs out of watches."
        fi
    else
        echo "✅ Current inotify watch limit is sufficient: $CURRENT_LIMIT"
    fi
else
    echo "⚠️  increase_inotify_limit.sh script not found. Skipping limit check."
fi

# Build command with appropriate options
CMD="streamlit run app.py"

# Add file watching optimization environment variables
if [ "$DISABLE_FILE_WATCHING" = true ]; then
    echo "📝 File watching disabled to improve performance"
    CMD="STREAMLIT_SERVER_FILE_WATCHER_TYPE=none $CMD -- --disable-file-watching"
else
    echo "📝 File watching enabled (may consume more system resources)"
    CMD="STREAMLIT_RUNTIME_WATCH_EXCLUDE='^.*\.meta' STREAMLIT_WATCHER_MAX_FILE_CHANGES=10 STREAMLIT_WATCHER_DEBOUNCE=0.5 $CMD"
fi

# Add flash enablement by default
if [ "$ENABLE_FLASH" = true ]; then
    echo "⚡ Flash functionality enabled"
    CMD="$CMD -- --enable-flash"
else
    echo "⚡ Flash functionality disabled"
fi

# Launch the application
echo "🚀 Starting Jetson Build Manager..."
echo "Command: $CMD"
eval $CMD
