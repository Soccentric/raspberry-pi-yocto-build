import streamlit as st
import subprocess
import os
import re
import time
from datetime import datetime
import glob
import sys

# Set page configuration
st.set_page_config(
    page_title="Jetson Build Manager",
    page_icon="🤖",
    layout="wide",
)

# Check inotify watches limit
def check_inotify_limit():
    try:
        max_watches = int(subprocess.check_output(["cat", "/proc/sys/fs/inotify/max_user_watches"]).decode("utf-8").strip())
        if max_watches < 8192:
            st.warning("""
            ⚠️ **Low inotify watches limit detected!**
            
            Your system has a low limit for inotify watches which may cause the application to crash.
            Please run the following command to increase the limit:
            
            ```bash
            sudo sh ./increase_inotify_limit.sh
            ```
            """)
    except Exception as e:
        # Silently pass if we can't check (permission issues, etc.)
        pass

# Function to read configuration from .env file
def read_env_config():
    config = {
        'KAS_FILE': 'kas/kas-poky-jetson.yml',
        'KAS_MACHINE': 'raspberrypi4',
        'KAS_DISTRO': 'poky',
        'KAS_IMAGE': 'core-image-base',
        'KAS_REPOS_FILE': 'common.yml',
        'KAS_LOCAL_CONF_FILE': 'local.yml',
        'KAS_BBLAYERS_FILE': 'bblayers.yml',
    }
    
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    
    return config

# Function to save configuration to .env file
def save_env_config(config):
    with open('.env', 'w') as f:
        for key, value in config.items():
            f.write(f"{key}={value}\n")
    st.success("Configuration saved successfully!")

# Function to run make command and stream output
def run_make_command(command, args=None):
    cmd = ['make', command]
    if args:
        cmd.extend(args)
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    output_placeholder = st.empty()
    output = ""
    
    # Create a container with fixed height and scrolling for console output
    with output_placeholder.container():
        console_output = st.empty()
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                output += line
                # Ensure proper HTML escaping to preserve line endings
                html_safe_output = output.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                # Apply CSS styling with fixed height, preserve whitespace, and auto-scroll to bottom
                console_output.markdown(f"""
                <div id="console-output" style="height: 400px; overflow-y: auto; font-family: monospace; background-color: #f0f0f0; padding: 10px; border-radius: 5px;">
                <pre style="white-space: pre; overflow-x: auto; line-height: 1.6em; margin: 0;">{html_safe_output}</pre>
                </div>
                <script>
                    // Auto-scroll to bottom of console output
                    var element = document.getElementById('console-output');
                    element.scrollTop = element.scrollHeight;
                </script>
                """, unsafe_allow_html=True)
    
    return_code = process.wait()
    
    if return_code == 0:
        st.success(f"Command completed successfully!")
    else:
        st.error(f"Command failed with return code {return_code}")
    
    return return_code, output

# Function to get list of artifacts
def get_artifacts():
    artifacts = []
    if os.path.exists('artifacts'):
        directories = [d for d in os.listdir('artifacts') if os.path.isdir(os.path.join('artifacts', d)) and re.match(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}', d)]
        directories.sort(reverse=True)
        
        for directory in directories:
            path = os.path.join('artifacts', directory)
            images_path = os.path.join(path, 'images')
            
            if os.path.exists(images_path):
                image_files = glob.glob(f"{images_path}/*")
                artifacts.append({
                    'date': directory,
                    'path': path,
                    'images': image_files,
                    'count': len(image_files)
                })
    
    return artifacts

# Main app
def main():
    # Check inotify limit at startup
    check_inotify_limit()
    
    st.title("🤖 Jetson Build Manager")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Build Configuration", "Build & Execute", "Artifacts", "System Info"])
    
    # Add a warning about filesystem watching in sidebar
    st.sidebar.info("If you experience crashes related to 'inotify watch limit reached', run the increase_inotify_limit.sh script.")
    
    # Read current configuration
    config = read_env_config()
    
    if page == "Build Configuration":
        st.header("Build Configuration")
        st.info("Configure essential build parameters. These will be saved to the .env file.")
        
        # Simplified configuration with only distro, machine and image
        config['KAS_MACHINE'] = st.text_input("Machine", config.get('KAS_MACHINE', 'raspberrypi4'))
        config['KAS_DISTRO'] = st.text_input("Distribution", config.get('KAS_DISTRO', 'poky'))
        config['KAS_IMAGE'] = st.text_input("Image", config.get('KAS_IMAGE', 'core-image-base'))
        
        if st.button("Save Configuration"):
            save_env_config(config)
    
    elif page == "Build & Execute":
        st.header("Build & Execute")
        
        # Display current configuration
        st.subheader("Current Configuration")
        st.code(f"KAS_FILE: {config.get('KAS_FILE')}\n"
                f"KAS_MACHINE: {config.get('KAS_MACHINE')}\n"
                f"KAS_DISTRO: {config.get('KAS_DISTRO')}\n"
                f"KAS_IMAGE: {config.get('KAS_IMAGE')}")
        
        # Build options
        st.subheader("Build Options")
        build_options = st.radio(
            "Select Build Type",
            ["Standard Build", "Build with SDK", "Build with Extensible SDK"]
        )
        
        compress_artifacts = st.checkbox("Compress Artifacts", value=False)
        
        # Execute button
        if st.button("Start Build", key="start_build"):
            st.info(f"Starting build at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            cmd_args = []
            if compress_artifacts:
                cmd_args.extend(["COMPRESS=1"])
                
            if build_options == "Standard Build":
                run_make_command("build", cmd_args)
            elif build_options == "Build with SDK":
                run_make_command("sdk", cmd_args)
            elif build_options == "Build with Extensible SDK":
                run_make_command("esdk", cmd_args)
    
    elif page == "Artifacts":
        st.header("📦 Build Artifacts")
        
        artifacts = get_artifacts()
        if not artifacts:
            st.info("No build artifacts found. Run a build to generate artifacts.")
        else:
            st.success(f"Found {len(artifacts)} artifact directories")
            
            # Add a search box
            search_term = st.text_input("🔍 Filter artifacts by name", "")
            
            # Display artifacts in a more visually appealing way
            for i, artifact in enumerate(artifacts):
                # Filter based on search term
                if search_term and not any(search_term.lower() in os.path.basename(img).lower() for img in artifact['images']):
                    continue
                
                # Use a colorful header for each artifact
                header_color = "#2E86C1" if i % 2 == 0 else "#5D6D7E"
                with st.expander(f"📅 {artifact['date']} - {artifact['count']} files"):
                    # Add a container to improve layout
                    with st.container():
                        # Improve the artifact path display
                        st.markdown(f"""
                        <div style="background-color:#f0f0f0; padding:10px; border-radius:5px; margin-bottom:10px;">
                            <b>📁 Path:</b> <code>{artifact['path']}</code><br>
                            <b>🕒 Date:</b> {artifact['date'].replace('_', ' ').replace('-', ':')}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if artifact['images']:
                            st.markdown("### 📊 Available Images")
                            
                            # Create columns for better layout of multiple images
                            cols = st.columns(2)
                            for idx, image in enumerate(artifact['images']):
                                filename = os.path.basename(image)
                                filesize = os.path.getsize(image) / (1024*1024)  # Convert to MB
                                col_idx = idx % 2
                                
                                # Create a card-like display for each image
                                with cols[col_idx]:
                                    st.markdown(f"""
                                    <div style="background-color:#eef2f5; padding:15px; border-radius:8px; margin-bottom:10px; border-left:4px solid {header_color};">
                                        <h4 style="margin:0; color:{header_color};">📄 {filename}</h4>
                                        <p style="margin:5px 0;"><b>Size:</b> {filesize:.2f} MB</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    if st.button(f"⚡ Flash {filename}", key=filename):
                                        st.warning("Flash functionality not implemented in the web UI for safety reasons.")
                                    
                                    # Add a download button
                                    with open(image, "rb") as file:
                                        st.download_button(
                                            label=f"⬇️ Download {filename}",
                                            data=file,
                                            file_name=filename,
                                            key=f"download_{filename}"
                                        )
    
    elif page == "System Info":
        st.header("System Information")
        
        # Run the makefile info command
        run_make_command("info")

        # Additional system info
        st.subheader("Disk Usage")
        disk_usage = subprocess.check_output(["df", "-h", "."]).decode('utf-8')
        st.code(disk_usage)
        
        st.subheader("Memory Usage")
        memory_usage = subprocess.check_output(["free", "-h"]).decode('utf-8')
        st.code(memory_usage)

# Try to execute app with error handling
if __name__ == "__main__":
    try:
        # Add command line argument parsing
        import argparse
        parser = argparse.ArgumentParser(description="Jetson Build Manager")
        parser.add_argument("--disable-file-watching", action="store_true", 
                            help="Disable file watching to reduce inotify watch usage")
        args = parser.parse_args()
        
        # If disable-file-watching is set, configure Streamlit to minimize file watching
        if args.disable_file_watching:
            import os
            os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"
            st.sidebar.warning("⚠️ File watching is disabled. You must manually refresh the page after making changes.")
        
        main()
    except OSError as e:
        if "inotify watch limit reached" in str(e):
            st.error("""
            ### Error: inotify watch limit reached
            
            The application crashed because your system ran out of inotify watches.
            To fix this issue:
            
            1. Run the `increase_inotify_limit.sh` script:
               ```
               sudo sh ./increase_inotify_limit.sh
               ```
            
            2. Or restart with reduced file watching:
               ```
               bash ./run_app.sh
               ```
            
            3. Or start with file watching disabled:
               ```
               streamlit run app.py -- --disable-file-watching
               ```
            """)
        else:
            st.error(f"Application error: {str(e)}")
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
