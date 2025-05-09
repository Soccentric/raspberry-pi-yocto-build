# 🤖 Jetson Build Manager

A web-based interface for managing Jetson builds with Yocto/KAS.

## Requirements

- Python 3.8 or higher
- Streamlit
- File system permissions to run builds

## Quick Start

The recommended way to start the application is using the launcher script:

```bash
bash ./run_app.sh
```

This will:

1. Check if your inotify watch limits are sufficient
2. Offer to increase them if needed
3. Start the application with optimized file watching settings

## Troubleshooting

### Inotify Watch Limit Issues

If you encounter errors about "inotify watch limit reached", you have several options:

1. **Increase the system limits** (recommended for development machines):

   ```bash
   sudo bash ./increase_inotify_limit.sh
   ```

2. **Run with reduced file watching** (recommended for most users):

   ```bash
   bash ./run_app.sh
   ```

3. **Disable file watching completely** (for resource-constrained environments):
   ```bash
   streamlit run app.py -- --disable-file-watching
   ```

### Manual Environment Variables

For advanced users who want to fine-tune the file watching behavior:

```bash
# Exclude certain patterns from being watched
export STREAMLIT_RUNTIME_WATCH_EXCLUDE="^.*\.meta"

# Reduce the number of file changes processed at once
export STREAMLIT_WATCHER_MAX_FILE_CHANGES=10

# Increase debounce time for file change events
export STREAMLIT_WATCHER_DEBOUNCE=0.5

# Start the app
streamlit run app.py
```

## Usage

Navigate to the different sections of the application using the sidebar:

1. **Build Configuration**: Set up your build parameters
2. **Build & Execute**: Start builds with various options
3. **Artifacts**: Browse and download build artifacts
4. **System Info**: View system and environment information

## License

Internal use only.
