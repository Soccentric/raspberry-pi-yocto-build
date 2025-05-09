import streamlit as st
import subprocess
import os
import re
import time
from datetime import datetime
import glob

# Set page configuration
st.set_page_config(
    page_title="Jetson Build Manager",
    page_icon="🤖",
    layout="wide",
)

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
    
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
        if line:
            output += line
            output_placeholder.code(output)
    
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
    st.title("🤖 Jetson Build Manager")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Build Configuration", "Build & Execute", "Artifacts", "System Info"])
    
    # Read current configuration
    config = read_env_config()
    
    if page == "Build Configuration":
        st.header("Build Configuration")
        st.info("Configure build parameters. These will be saved to the .env file.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            config['KAS_FILE'] = st.text_input("KAS File", config.get('KAS_FILE', 'kas/kas-poky-jetson.yml'))
            config['KAS_MACHINE'] = st.text_input("Machine", config.get('KAS_MACHINE', 'raspberrypi4'))
            config['KAS_DISTRO'] = st.text_input("Distribution", config.get('KAS_DISTRO', 'poky'))
            config['KAS_IMAGE'] = st.text_input("Image", config.get('KAS_IMAGE', 'core-image-base'))
        
        with col2:
            config['KAS_REPOS_FILE'] = st.text_input("Repos File", config.get('KAS_REPOS_FILE', 'common.yml'))
            config['KAS_LOCAL_CONF_FILE'] = st.text_input("Local Conf File", config.get('KAS_LOCAL_CONF_FILE', 'local.yml'))
            config['KAS_BBLAYERS_FILE'] = st.text_input("BBLayers File", config.get('KAS_BBLAYERS_FILE', 'bblayers.yml'))
        
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
        st.header("Build Artifacts")
        
        artifacts = get_artifacts()
        if not artifacts:
            st.info("No build artifacts found. Run a build to generate artifacts.")
        else:
            st.success(f"Found {len(artifacts)} artifact directories")
            
            for artifact in artifacts:
                with st.expander(f"{artifact['date']} - {artifact['count']} files"):
                    st.write(f"Path: {artifact['path']}")
                    if artifact['images']:
                        st.write("Images:")
                        for image in artifact['images']:
                            filename = os.path.basename(image)
                            filesize = os.path.getsize(image) / (1024*1024)  # Convert to MB
                            st.code(f"{filename} ({filesize:.2f} MB)")
                            
                            if st.button(f"Flash {filename}", key=filename):
                                st.warning("Flash functionality not implemented in the web UI for safety reasons.")
    
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

# Execute app
if __name__ == "__main__":
    main()
