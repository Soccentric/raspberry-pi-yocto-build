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

# Function to flash an image to a device
def flash_image(image_path, device=None):
    st.info(f"Preparing to flash {os.path.basename(image_path)}...")
    
    if device is None:
        # Get list of available devices
        try:
            output = subprocess.check_output(["lsblk", "-d", "-n", "-o", "NAME,SIZE,MODEL"]).decode('utf-8')
            devices = []
            for line in output.strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 2 and not parts[0].startswith('loop'):
                        devices.append({
                            'name': parts[0],
                            'size': parts[1],
                            'model': ' '.join(parts[2:]) if len(parts) > 2 else 'Unknown'
                        })
            
            if not devices:
                st.error("No suitable devices found for flashing")
                return False
                
            # Let user select a device
            device_options = [f"{d['name']} ({d['size']}) - {d['model']}" for d in devices]
            selected = st.selectbox("Select target device:", device_options)
            device = "/dev/" + selected.split()[0]
        except Exception as e:
            st.error(f"Error detecting devices: {str(e)}")
            return False
    
    # Confirm before flashing
    st.warning(f"⚠️ You are about to flash {os.path.basename(image_path)} to {device}. This will ERASE ALL DATA on the device!")
    
    col1, col2 = st.columns(2)
    with col1:
        confirm = st.checkbox("I understand and confirm this action")
    with col2:
        if confirm and st.button("Start Flashing", type="primary"):
            # Use dd to flash the image
            try:
                with st.spinner(f"Flashing to {device}. Please wait..."):
                    # Command will depend on the image type
                    if image_path.endswith('.wic') or image_path.endswith('.img'):
                        flash_cmd = ["sudo", "dd", f"if={image_path}", f"of={device}", "bs=4M", "status=progress", "conv=fsync"]
                    elif image_path.endswith('.bz2'):
                        flash_cmd = ["sudo", "bash", "-c", f"bunzip2 -c {image_path} | dd of={device} bs=4M status=progress conv=fsync"]
                    else:
                        flash_cmd = ["sudo", "bash", "-c", f"cat {image_path} | dd of={device} bs=4M status=progress conv=fsync"]
                    
                    result = subprocess.run(flash_cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        st.success(f"Successfully flashed {os.path.basename(image_path)} to {device}")
                        # Try to sync to ensure data is written
                        subprocess.run(["sudo", "sync"])
                        return True
                    else:
                        st.error(f"Error during flashing: {result.stderr}")
                        return False
            except Exception as e:
                st.error(f"Flash error: {str(e)}")
                return False
    return False

# Main app
def main():
    # Check inotify limit at startup
    check_inotify_limit()
    
    st.title("🤖 Jetson Build Manager")
    
    # Use a cleaner sidebar style
    st.sidebar.markdown("""
    <style>
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Simplified sidebar navigation with clean styling
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("", ["Build Configuration", "Build & Execute", "Artifacts", "System Info"], 
                            format_func=lambda x: f"{x}")
    
    # Add a simplified warning about filesystem watching in sidebar
    st.sidebar.info("Run increase_inotify_limit.sh if you experience crashes.")
    
    # Read current configuration
    config = read_env_config()
    
    # Parse command-line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Jetson Build Manager")
    parser.add_argument("--disable-file-watching", action="store_true", 
                        help="Disable file watching to reduce inotify watch usage")
    parser.add_argument("--enable-flash", action="store_true",
                        help="Enable flash functionality (use with caution)")
    args = parser.parse_args()
    
    # Set global flash enabled flag
    flash_enabled = args.enable_flash
    
    if page == "Build Configuration":
        st.header("Build Configuration")
        st.text("Configure essential build parameters.")
        
        # Simplified configuration with only distro, machine and image in a cleaner layout
        col1, col2 = st.columns([1, 2])
        with col1:
            st.text("Machine:")
            st.text("Distribution:")
            st.text("Image:")
        with col2:
            config['KAS_MACHINE'] = st.text_input("", config.get('KAS_MACHINE', 'raspberrypi4'), key="machine_input", label_visibility="collapsed")
            config['KAS_DISTRO'] = st.text_input("", config.get('KAS_DISTRO', 'poky'), key="distro_input", label_visibility="collapsed")
            config['KAS_IMAGE'] = st.text_input("", config.get('KAS_IMAGE', 'core-image-base'), key="image_input", label_visibility="collapsed")
        
        # Use a cleaner button style
        if st.button("Save", type="primary"):
            save_env_config(config)
    
    elif page == "Build & Execute":
        st.header("Build & Execute")
        
        # Display current configuration in a simpler format
        st.subheader("Current Configuration")
        
        # Create a simple table-like display
        col1, col2 = st.columns([1, 3])
        with col1:
            st.text("File:")
            st.text("Machine:")
            st.text("Distribution:")
            st.text("Image:")
        with col2:
            st.text(config.get('KAS_FILE'))
            st.text(config.get('KAS_MACHINE'))
            st.text(config.get('KAS_DISTRO'))
            st.text(config.get('KAS_IMAGE'))
        
        # Build options with simplified styling
        st.subheader("Build Options")
        build_options = st.radio(
            "",
            ["Standard Build", "Build with SDK", "Build with Extensible SDK"],
            label_visibility="collapsed"
        )
        
        compress_artifacts = st.checkbox("Compress Artifacts")
        
        # Execute button with cleaner styling
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("Start Build", type="primary", key="start_build"):
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
        st.header("Build Artifacts")
        
        # Display flash functionality warning
        if flash_enabled:
            st.warning("⚠️ Flash functionality is enabled. Use with caution.")
        else:
            st.info("Flash functionality is disabled. Start with --enable-flash to enable it.")
        
        artifacts = get_artifacts()
        if not artifacts:
            st.info("No build artifacts found. Run a build to generate artifacts.")
        else:
            # Simplified success message
            st.text(f"Found {len(artifacts)} artifact directories")
            
            # Simplified search box
            search_term = st.text_input("Filter artifacts", "")
            
            # Display artifacts in a simpler, flatter layout
            for i, artifact in enumerate(artifacts):
                # Filter based on search term
                if search_term and not any(search_term.lower() in os.path.basename(img).lower() for img in artifact['images']):
                    continue
                
                # Simplified expander without emoji and with minimal styling
                with st.expander(f"{artifact['date']} - {artifact['count']} files", key=f"artifact_{artifact['date']}"):
                    # Add simple layout
                    st.text(f"Path: {artifact['path']}")
                    st.text(f"Date: {artifact['date'].replace('_', ' ').replace('-', ':')}")
                    
                    if artifact['images']:
                        st.subheader("Available Images")
                        
                        # Use a simpler table layout
                        for image in artifact['images']:
                            filename = os.path.basename(image)
                            filesize = os.path.getsize(image) / (1024*1024)  # Convert to MB
                            
                            # Create a simple card
                            st.text(f"{filename} ({filesize:.2f} MB)")
                            col1, col2 = st.columns([1, 1])
                            with col1:
                                if flash_enabled:
                                    if st.button("Flash", key=f"flash_{artifact['date']}_{filename}"):
                                        flash_image(image)
                                else:
                                    st.button("Flash", key=f"flash_{artifact['date']}_{filename}", disabled=True)
                            with col2:
                                with open(image, "rb") as file:
                                    st.download_button(
                                        "Download",
                                        data=file,
                                        file_name=filename,
                                        key=f"download_{artifact['date']}_{filename}"
                                    )
                            st.divider()
    
    elif page == "System Info":
        st.header("System Information")
        
        # Run the makefile info command
        run_make_command("info")

        # Simple system info
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Disk Usage")
            disk_usage = subprocess.check_output(["df", "-h", "."]).decode('utf-8')
            st.code(disk_usage)
        with col2:
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
        parser.add_argument("--enable-flash", action="store_true",
                            help="Enable flash functionality (use with caution)")
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
