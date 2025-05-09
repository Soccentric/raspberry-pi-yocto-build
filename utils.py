import os
import re
import subprocess
import streamlit as st

def read_env_file():
    env_vars = {}
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"\'')
    return env_vars

def save_env_file(env_vars):
    with open('.env', 'w') as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    st.success("Configuration saved to .env file!")

def get_makefile_options():
    try:
        with open("Makefile", "r") as f:
            makefile = f.read()
            
        kas_machine_match = re.search(r'KAS_MACHINE \?= (.+)', makefile)
        kas_distro_match = re.search(r'KAS_DISTRO \?= (.+)', makefile)
        kas_image_match = re.search(r'KAS_IMAGE \?= (.+)', makefile)
        
        defaults = {
            "KAS_MACHINE": kas_machine_match.group(1) if kas_machine_match else "",
            "KAS_DISTRO": kas_distro_match.group(1) if kas_distro_match else "",
            "KAS_IMAGE": kas_image_match.group(1) if kas_image_match else "",
        }
        
        # For other KAS_ vars that are not in sidebar but needed for .env
        for var_name in ["KAS_FILE", "KAS_REPOS_FILE", "KAS_LOCAL_CONF_FILE", "KAS_BBLAYERS_FILE"]:
            match = re.search(rf'{var_name} \?= (.+)', makefile)
            if match:
                defaults[var_name] = match.group(1)

        # Extract available targets/commands (simplified, as it's not directly used by UI anymore)
        targets = {} # Placeholder, can be expanded if needed
        
        return defaults, targets
    except Exception as e:
        st.error(f"Error parsing Makefile: {e}")
        return {}, {}

def list_available_images():
    try:
        # Assuming Makefile is in the same directory
        result = subprocess.run(["make", "list-images"], capture_output=True, text=True, check=False)
        images = []
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if '.wic' in line or '.sdimg' in line or '.rpi-sdimg' in line:
                    images.append(line.strip())
        else:
            st.warning(f"Could not list images: {result.stderr}")
        return images
    except Exception as e:
        st.error(f"Error listing images: {e}")
        return []

def get_build_status():
    try:
        # Assuming Makefile is in the same directory
        result = subprocess.run(["make", "status"], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error getting status: {result.stderr}"
    except Exception as e:
        st.error(f"Error getting build status: {e}")
        return ""

def get_build_info_raw():
    try:
        result = subprocess.run(["make", "info"], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error getting info: {result.stderr}"
    except Exception as e:
        return f"Failed to execute 'make info': {e}"

