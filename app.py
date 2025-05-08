import streamlit as st
import subprocess
import os
import yaml
import glob
import time
import psutil
import datetime
import base64
from pathlib import Path
import platform

# Get the absolute path of the directory where app.py is located
# This ensures that 'make' commands are run from the project root.
APP_DIR = os.path.dirname(os.path.abspath(__file__))
MAKEFILE_PATH = os.path.join(APP_DIR, "Makefile")
KAS_DIR = os.path.join(APP_DIR, "kas")

def run_make_command(command, env_vars=None):
    """Runs a make command and streams the output.
    
    Args:
        command (str): The make command to run
        env_vars (dict, optional): Environment variables to pass to the make command
    """
    # Create environment variables string for display
    env_str = ""
    env = os.environ.copy()
    
    if env_vars:
        for key, value in env_vars.items():
            env[key] = value
            env_str += f"{key}={value} "
    
    cmd_str = f"{env_str}make {command}"
    st.info(f"Running: {cmd_str}")
    
    progress_bar = st.progress(0)
    output_placeholder = st.empty()
    full_output = []

    try:
        process = subprocess.Popen(
            ["make", command],
            cwd=APP_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )

        for i, line in enumerate(iter(process.stdout.readline, "")):
            full_output.append(line)
            # Update progress bar (simple animation)
            progress_bar.progress(min((i % 100) + 1, 100))
            # Display live output
            output_placeholder.text_area("Live Output:", "".join(full_output), height=300, key=f"output_{command}_{i}")

        process.stdout.close()
        return_code = process.wait()
        progress_bar.empty() # Remove progress bar after completion

        if return_code == 0:
            st.success(f"Command 'make {command}' completed successfully!")
        else:
            st.error(f"Command 'make {command}' failed with exit code {return_code}.")
        
        output_placeholder.text_area("Final Output:", "".join(full_output), height=300, key=f"final_output_{command}")
        return "".join(full_output), return_code

    except FileNotFoundError:
        st.error(f"Error: 'make' command not found. Please ensure Make is installed and in your PATH.")
        return "", -1
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return "".join(full_output), -1


# UI Helper Functions
def local_css():
    """Apply custom CSS styles to the app."""
    st.markdown("""
    <style>
        .stApp {
            background-color: #f5f7fa;
        }
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        h1, h2, h3 {
            color: #1E3A8A;
        }
        .stButton button {
            border-radius: 8px;
            font-weight: 500;
        }
        .card {
            border-radius: 10px;
            background-color: white;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
        .info-metric {
            padding: 0.75rem;
            background-color: #f0f9ff;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 1rem;
        }
        .metric-value {
            font-size: 1.5rem;
            font-weight: bold;
            color: #0369a1;
        }
        .metric-label {
            font-size: 0.85rem;
            color: #64748b;
        }
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 500;
        }
        .status-badge.success {
            background-color: #dcfce7;
            color: #166534;
        }
        .status-badge.warning {
            background-color: #fef3c7;
            color: #92400e;
        }
        .status-badge.error {
            background-color: #fee2e2;
            color: #b91c1c;
        }
        .status-badge.info {
            background-color: #e0f2fe;
            color: #075985;
        }
        .sidebar-header {
            margin-top: 0;
            padding-top: 0;
            margin-bottom: 1rem;
        }
        .logo-text {
            font-weight: 700;
            color: #1e40af;
            font-size: 1.25rem;
        }
        .custom-progress-bar {
            height: 0.75rem;
            border-radius: 0.375rem;
        }
        .custom-tabs .stTabs [data-baseweb="tab-list"] {
            gap: 1rem;
        }
        .custom-tabs .stTabs [data-baseweb="tab"] {
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
        }
    </style>
    """, unsafe_allow_html=True)

def get_file_download_link(file_path, link_text="Download"):
    """Generate a link to download a file."""
    with open(file_path, "rb") as f:
        data = f.read()
    b64_data = base64.b64encode(data).decode()
    file_name = os.path.basename(file_path)
    return f'<a href="data:application/octet-stream;base64,{b64_data}" download="{file_name}">{link_text}</a>'

def get_system_metrics():
    """Get system metrics for display in the dashboard."""
    metrics = {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "disk_free": round(psutil.disk_usage("/").free / (1024.0 ** 3), 2),  # GB
        "memory_total": round(psutil.virtual_memory().total / (1024.0 ** 3), 2),  # GB
        "cpu_count": os.cpu_count() or psutil.cpu_count(),
        "system": platform.system(),
        "hostname": platform.node(),
    }
    return metrics

def display_metric(label, value, unit="", container=None):
    """Display a metric in a nicely formatted way."""
    target = container or st
    target.markdown(f"""
    <div class="info-metric">
        <div class="metric-value">{value}{unit}</div>
        <div class="metric-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)

def generate_build_timestamp():
    """Generate a timestamp for build identification."""
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

def load_configurations():
    """Load KAS configurations from the kas directory."""
    configurations = {
        "machines": sorted([os.path.basename(f).replace('.yml', '') 
                     for f in glob.glob(os.path.join(KAS_DIR, "machines", "*.yml"))]),
        "distros": sorted([os.path.basename(f).replace('.yml', '') 
                    for f in glob.glob(os.path.join(KAS_DIR, "distros", "*.yml"))]),
        "images": sorted([os.path.basename(f).replace('.yml', '') 
                   for f in glob.glob(os.path.join(KAS_DIR, "images", "*.yml"))])
    }
    return configurations


st.set_page_config(
    page_title="Embedded Linux Builder", 
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/embedded-linux-builder',
        'Report a bug': 'https://github.com/yourusername/embedded-linux-builder/issues',
        'About': "# Embedded Linux Builder\nA modern UI for building custom embedded Linux images with Kas/Yocto."
    }
)

# Apply custom CSS
local_css()

# Sidebar setup with improved design
with st.sidebar:
    st.markdown('<div class="sidebar-header"><span class="logo-text">🛠️ Embedded Linux Builder</span></div>', unsafe_allow_html=True)
    
    # Build history navigation
    st.markdown("### 📊 Dashboard")
    dashboard_page = st.sidebar.selectbox(
        "View",
        ["Builder", "System Monitor", "Build History", "Settings"],
        index=0,
        key="dashboard_selector"
    )
    
    st.markdown("### 🖥️ System Info")
    metrics = get_system_metrics()
    
    # System metrics in sidebar
    col1, col2 = st.columns(2)
    with col1:
        display_metric("CPU Usage", f"{metrics['cpu_percent']}","%")
    with col2:
        display_metric("Memory", f"{metrics['memory_percent']}", "%")
    
    col1, col2 = st.columns(2)
    with col1:
        display_metric("Disk Free", f"{metrics['disk_free']}", "GB")
    with col2:
        display_metric("CPUs", f"{metrics['cpu_count']}")
    
    # Check if Docker is available
    docker_available = subprocess.run(
        ["which", "docker"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).returncode == 0
    
    st.markdown(f"""
    <div style="margin-top: 1rem;">
        <span class="status-badge {'success' if docker_available else 'error'}">
            {'✅ Docker Available' if docker_available else '❌ Docker Missing'}
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # Add a refresh button for configurations
    st.markdown("### 🔄 Actions")
    if st.button("Refresh Configurations", use_container_width=True):
        st.cache_data.clear()
        st.toast("Configuration cache cleared!")
        st.rerun()

# Main content based on dashboard selection
if dashboard_page == "Builder":
    # Main header
    st.markdown('<h1 style="text-align: center;">Embedded Linux Builder</h1>', unsafe_allow_html=True)
    
    # Introduction with improved design
    st.markdown('''
    <div class="card">
        <h3>Welcome to the Embedded Linux Builder</h3>
        <p>
            This application provides a modern interface for building custom embedded Linux 
            images using the Kas build system. Select your configuration options below 
            and start building your custom image with ease.
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Build timestamp for identification
    build_id = generate_build_timestamp()

# Load configurations using caching for better performance
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_cached_configurations():
    return load_configurations()

configurations = get_cached_configurations()

# Main configuration section with modern card design
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<h2>📋 Build Configuration</h2>', unsafe_allow_html=True)

# Build config tabs for better organization
config_tabs = st.tabs(["Hardware & Image", "Build Options", "Advanced Settings"])

with config_tabs[0]:
    st.markdown("### 🔧 Select your target platform and image")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Target Hardware")
        if configurations["machines"]:
            machine_options = configurations["machines"]
            machine_icons = {name: "🖥️" for name in machine_options}
            machine_display = [f"{machine_icons.get(m, '🖥️')} {m}" for m in machine_options]
            
            selected_machine = st.selectbox(
                "Select Machine",
                range(len(machine_options)),
                format_func=lambda i: machine_display[i],
                index=0
            )
            machine = machine_options[selected_machine]
            
            st.info(f"Selected machine: **{machine}**")
        else:
            st.error("No machine configurations found!")
            machine = None
    
    with col2:
        st.markdown("#### Distribution")
        if configurations["distros"]:
            distro_options = configurations["distros"]
            distro_icons = {name: "📦" for name in distro_options}
            distro_display = [f"{distro_icons.get(d, '📦')} {d}" for d in distro_options]
            
            selected_distro = st.selectbox(
                "Select Distribution",
                range(len(distro_options)),
                format_func=lambda i: distro_display[i],
                index=0
            )
            distro = distro_options[selected_distro]
            
            st.info(f"Selected distro: **{distro}**")
        else:
            st.error("No distro configurations found!")
            distro = None
    
    with col3:
        st.markdown("#### Image Type")
        if configurations["images"]:
            image_options = configurations["images"]
            image_icons = {
                name: "💿" if "iso" in name.lower() else 
                      "💾" if "sdcard" in name.lower() else 
                      "📱" for name in image_options
            }
            image_display = [f"{image_icons.get(i, '📱')} {i}" for i in image_options]
            
            selected_image = st.selectbox(
                "Select Image",
                range(len(image_options)),
                format_func=lambda i: image_display[i],
                index=0
            )
            image = image_options[selected_image]
            
            st.info(f"Selected image: **{image}**")
        else:
            st.error("No image configurations found!")
            image = None

# Build options in tab interface
with config_tabs[1]:
    st.markdown("### ⚙️ Configure your build process")
    
    build_cols = st.columns(2)
    
    with build_cols[0]:
        st.markdown("#### Build Type")
        build_type = st.radio(
            "Select build type",
            ["Standard", "Clean", "Incremental"],
            horizontal=True,
            index=0,
            help="Standard: Normal build, Clean: Remove all previous artifacts, Incremental: Continue previous build"
        )
        clean_build = build_type == "Clean"
        
        st.markdown("#### Output Options")
        verbose = st.toggle(
            "Verbose Output",
            value=False,
            help="Show detailed build output for debugging"
        )
    
    with build_cols[1]:
        st.markdown("#### Performance")
        
        # Get the number of CPU cores for default parallel jobs
        cpu_cores = metrics['cpu_count']
        recommended_jobs = max(1, cpu_cores - 1)  # Leave one core for system
        
        parallel_jobs = st.slider(
            "Parallel Jobs",
            min_value=1,
            max_value=max(cpu_cores*2, 8),
            value=recommended_jobs,
            help=f"Recommended: {recommended_jobs} (1 less than your CPU cores)"
        )
        
        st.markdown("#### Debugging")
        debug_build = st.toggle(
            "Include Debug Symbols",
            value=False,
            help="Create a debug build with symbols (larger size)"
        )
        
        # Add estimated disk space requirement
        st.info(f"💾 Estimated disk space needed: {10 + (5 if debug_build else 0)}+ GB")

# Advanced options in tab interface
with config_tabs[2]:
    st.markdown("### 🔍 Advanced Settings")
    
    st.markdown("#### Environment Variables")
    custom_env = st.text_area(
        "Custom Environment Variables (KEY=VALUE format)",
        placeholder="MACHINE_FEATURES=wifi bluetooth\nEXTRA_IMAGE_FEATURES=debug-tweaks",
        height=100,
        help="Add custom environment variables for the build process"
    )
    
    st.markdown("#### Build Arguments")
    custom_args = st.text_input(
        "Additional Make Arguments",
        placeholder="--no-checksum --warn-detect-undefined",
        help="Extra arguments to pass to the make command"
    )
    
    st.markdown("#### Build Identification")
    build_name = st.text_input(
        "Build Name (Optional)",
        placeholder=f"build-{machine}-{datetime.datetime.now().strftime('%Y%m%d')}",
        help="A custom name to identify this build"
    )

st.markdown('</div>', unsafe_allow_html=True)

# Build section with improved design
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<h2>🚀 Build & Deploy</h2>', unsafe_allow_html=True)

# Build action columns
build_action_col1, build_action_col2 = st.columns([2, 1])

with build_action_col2:
    # Configuration validation button with improved styling
    if st.button("✓ Validate Configuration", use_container_width=True):
        with st.spinner("Validating configuration..."):
            validation_env = {}
            if machine:
                validation_env["MACHINE"] = machine
            if distro:
                validation_env["DISTRO"] = distro
            if image:
                validation_env["IMAGE"] = image
                
            output, return_code = run_make_command("validate-config", env_vars=validation_env)
            
            if return_code == 0:
                st.success("✅ Configuration is valid! You can proceed with the build.")
            else:
                st.error("❌ Configuration validation failed. Check the output for details.")

# Main build button with progress tracking
with build_action_col1:
    # Use a form for the build to prevent accidental rebuilds
    with st.form(key="build_form"):
        build_button_text = "🚀 Start Build" if machine and distro and image else "Select Configuration First"
        build_button_disabled = not (machine and distro and image)
        
        submit_build = st.form_submit_button(
            build_button_text, 
            use_container_width=True,
            type="primary",
            disabled=build_button_disabled
        )
        
        if submit_build:
            if not (machine and distro and image):
                st.error("Please select Machine, Distro, and Image before building.")
            else:
                # Show build summary
                st.info(f"Building **{image}** for **{machine}** with **{distro}** distribution")
                
                # Prepare environment variables
                build_env = {
                    "MACHINE": machine,
                    "DISTRO": distro,
                    "IMAGE": image,
                    "PARALLEL_MAKE": f"-j {parallel_jobs}",
                    "BUILD_ID": build_id
                }
                
                # Add custom environment variables
                if custom_env:
                    for line in custom_env.strip().split("\n"):
                        if "=" in line:
                            key, value = line.split("=", 1)
                            build_env[key.strip()] = value.strip()
                
                # Determine build command
                build_cmd = ""
                if clean_build:
                    build_cmd = "clean all"
                else:
                    build_cmd = "all"
                    
                # Add custom arguments if provided
                if custom_args:
                    build_cmd += f" {custom_args}"
                    
                # Add verbose flag if selected
                if verbose:
                    build_env["VERBOSE"] = "1"
                    
                # Add debug flag if selected
                if debug_build:
                    build_env["DEBUG_BUILD"] = "1"
                
                # Save build details for history
                build_start_time = datetime.datetime.now()
                
                # Create a progress display
                progress_container = st.empty()
                with progress_container.container():
                    st.markdown("### 🔄 Building...")
                    status_cols = st.columns(4)
                    with status_cols[0]:
                        display_metric("Machine", machine)
                    with status_cols[1]:
                        display_metric("Distro", distro)
                    with status_cols[2]:
                        display_metric("Image", image)
                    with status_cols[3]:
                        display_metric("Build ID", build_id)
                    
                    # Progress and time trackers
                    progress_bar = st.progress(0)
                    time_container = st.empty()
                    start_time = time.time()
                    
                    # Run the build command with periodic UI updates
                    output, return_code = run_make_command(build_cmd, env_vars=build_env)
                    
                    # Clear the progress display after build completes
                    progress_container.empty()
                
                # Build finished, display results
                build_end_time = datetime.datetime.now()
                build_duration = (build_end_time - build_start_time).total_seconds()
                
                if return_code == 0:
                    st.balloons()
                    st.success(f"✅ Build completed successfully in {build_duration:.1f} seconds!")
                    
                    # Display image location and artifacts
                    output_dir = os.path.join(APP_DIR, "build", "tmp", "deploy", "images", machine)
                    if os.path.exists(output_dir):
                        st.info(f"📁 Built images are available in: `{output_dir}`")
                        
                        # Create a download section for built artifacts
                        st.markdown("### 📥 Download Build Artifacts")
                        
                        artifact_tabs = st.tabs(["Images", "Packages", "SDK"])
                        
                        with artifact_tabs[0]:
                            found_artifacts = False
                            for root, dirs, files in os.walk(output_dir):
                                for file in files:
                                    if file.endswith(('.wic', '.img', '.tar.bz2', '.ext4')):
                                        found_artifacts = True
                                        file_path = os.path.join(root, file)
                                        relative_path = os.path.relpath(file_path, output_dir)
                                        file_size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 1)
                                        
                                        col1, col2, col3 = st.columns([3, 1, 1])
                                        with col1:
                                            st.markdown(f"**{relative_path}**")
                                        with col2:
                                            st.markdown(f"{file_size_mb} MB")
                                        with col3:
                                            st.markdown(get_file_download_link(file_path, "Download"), unsafe_allow_html=True)
                            
                            if not found_artifacts:
                                st.info("No image files found in the output directory.")
                    else:
                        st.info("Output directory not found. Check build logs for details.")
                else:
                    st.error(f"❌ Build failed after {build_duration:.1f} seconds. Check the output for details.")
                    
                    # Display common error patterns and possible solutions
                    with st.expander("Troubleshooting"):
                        st.markdown("""
                        ### Common Build Issues
                        
                        1. **Missing dependencies** - Check if you have all required packages installed
                        2. **Disk space issues** - Ensure you have at least 50GB free space
                        3. **Network failures** - Some packages might have failed to download
                        4. **Permission issues** - Check if you have write permissions to the build directory
                        
                        Review the complete build log for more specific error details.
                        """)

st.markdown('</div>', unsafe_allow_html=True)

# Utilities section with cards layout
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<h2>🔧 Utilities & Tools</h2>', unsafe_allow_html=True)

# Utility tabs
util_tabs = st.tabs(["System Maintenance", "Environment", "Documentation"])

with util_tabs[0]:
    st.markdown("### System Maintenance Tools")
    
    maintenance_cols = st.columns(3)
    
    with maintenance_cols[0]:
        if st.button("🧹 Clean Build Directory", use_container_width=True):
            with st.spinner("Cleaning build directory..."):
                output, return_code = run_make_command("clean")
                if return_code == 0:
                    st.success("✅ Build directory cleaned successfully!")
                else:
                    st.error("❌ Failed to clean build directory.")
    
    with maintenance_cols[1]:
        if st.button("🧽 Clean Machine Output", use_container_width=True):
            with st.spinner(f"Cleaning output for {machine}..."):
                if machine:
                    output, return_code = run_make_command("cleanmachine", 
                                                          env_vars={"KAS_MACHINE": machine})
                    if return_code == 0:
                        st.success(f"✅ Output for {machine} cleaned!")
                    else:
                        st.error("❌ Failed to clean machine output.")
                else:
                    st.warning("⚠️ Please select a machine first.")
    
    with maintenance_cols[2]:
        if st.button("🔍 System Information", use_container_width=True):
            with st.spinner("Gathering system information..."):
                output, return_code = run_make_command("info")
                if return_code == 0:
                    st.code(output)
                else:
                    st.error("❌ Failed to get system information.")

with util_tabs[1]:
    st.markdown("### Build Environment")
    
    if st.button("📋 Show Complete Environment", key="show_env_button"):
        with st.spinner("Loading environment information..."):
            env_vars = {}
            if machine:
                env_vars["MACHINE"] = machine
            if distro:
                env_vars["DISTRO"] = distro
            if image:
                env_vars["IMAGE"] = image
                
            output, return_code = run_make_command("show-env", env_vars=env_vars)
            
            if return_code == 0:
                with st.expander("Environment Variables", expanded=True):
                    st.code(output)
            else:
                st.error("❌ Failed to show environment.")
    
    # Current configuration
    st.markdown("### Current Configuration")
    config_cols = st.columns(3)
    
    with config_cols[0]:
        st.markdown("**Hardware**")
        st.code(f"MACHINE={machine}" if machine else "Not selected")
    
    with config_cols[1]:
        st.markdown("**Software**")
        st.code(f"DISTRO={distro}" if distro else "Not selected")
    
    with config_cols[2]:
        st.markdown("**Image**")
        st.code(f"IMAGE={image}" if image else "Not selected")

with util_tabs[2]:
    st.markdown("### Documentation & Resources")
    
    st.markdown("""
    #### Yocto Project
    - [Yocto Project Documentation](https://docs.yoctoproject.org/)
    - [BitBake User Manual](https://docs.yoctoproject.org/bitbake/)
    
    #### Kas Build System
    - [Kas Documentation](https://kas.readthedocs.io/)
    - [Kas GitHub Repository](https://github.com/siemens/kas)
    
    #### Machine-Specific Resources
    - [Raspberry Pi Documentation](https://www.raspberrypi.com/documentation/)
    - [NVIDIA Jetson Documentation](https://docs.nvidia.com/jetson/)
    """)

st.markdown('</div>', unsafe_allow_html=True)

# Add System Monitor, Build History, and Settings tabs
if dashboard_page == "System Monitor":
    st.title("System Monitor")
    
    # System resource metrics
    st.markdown("### System Resources")
    
    # Real-time metrics
    metrics = get_system_metrics()
    
    metric_cols = st.columns(4)
    with metric_cols[0]:
        display_metric("CPU Usage", f"{metrics['cpu_percent']}", "%")
    with metric_cols[1]:
        display_metric("Memory Use", f"{metrics['memory_percent']}", "%")
    with metric_cols[2]:
        display_metric("Disk Usage", f"{metrics['disk_percent']}", "%")
    with metric_cols[3]:
        display_metric("Free Disk", f"{metrics['disk_free']}", "GB")
    
    # System information
    st.markdown("### System Information")
    
    info_cols = st.columns(2)
    with info_cols[0]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### Hardware Information")
        st.markdown(f"""
        - **System**: {metrics['system']}
        - **Hostname**: {metrics['hostname']}
        - **CPU Cores**: {metrics['cpu_count']}
        - **Memory Total**: {metrics['memory_total']} GB
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with info_cols[1]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### Build Environment")
        
        # Check required tools
        docker_available = subprocess.run(
            ["which", "docker"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).returncode == 0
        
        make_available = subprocess.run(
            ["which", "make"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).returncode == 0
        
        kas_available = subprocess.run(
            ["which", "kas"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).returncode == 0
        
        st.markdown(f"""
        - **Docker**: {'✅ Available' if docker_available else '❌ Missing'}
        - **Make**: {'✅ Available' if make_available else '❌ Missing'}
        - **Kas**: {'✅ Available' if kas_available else '❌ Missing'}
        - **Working Directory**: `{APP_DIR}`
        """)
        st.markdown('</div>', unsafe_allow_html=True)

elif dashboard_page == "Build History":
    st.title("Build History")
    
    # Placeholder for build history (in a real app, you'd store this in a database)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Recent Builds")
    
    st.info("Build history will be displayed here. In a production application, this would be stored in a database.")
    
    # Sample build history
    build_history = [
        {"id": "20250508-101523", "machine": "raspberrypi4", "distro": "poky", "image": "core-image-base", "status": "success", "date": "2025-05-08 10:15:23"},
        {"id": "20250507-143012", "machine": "jetson-nano", "distro": "poky-ml", "image": "ml-image", "status": "failed", "date": "2025-05-07 14:30:12"},
        {"id": "20250505-091845", "machine": "imx8", "distro": "poky-rt", "image": "core-image-minimal", "status": "success", "date": "2025-05-05 09:18:45"},
    ]
    
    for build in build_history:
        col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
        with col1:
            st.markdown(f"**{build['id']}**")
        with col2:
            st.markdown(f"{build['machine']} | {build['image']}")
        with col3:
            st.markdown(f"{build['date']}")
        with col4:
            status_class = "success" if build["status"] == "success" else "error"
            status_text = "✅ Success" if build["status"] == "success" else "❌ Failed"
            st.markdown(f'<span class="status-badge {status_class}">{status_text}</span>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

elif dashboard_page == "Settings":
    st.title("Settings")
    
    # Application settings
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Application Settings")
    
    settings_tabs = st.tabs(["General", "Build Defaults", "Storage"])
    
    with settings_tabs[0]:
        st.markdown("#### General Settings")
        st.toggle("Dark Mode", value=False, disabled=True, help="Enable dark mode (coming soon)")
        st.toggle("Auto-refresh System Monitor", value=True, help="Automatically refresh system metrics")
        st.slider("Refresh Interval (seconds)", 5, 60, 15)
    
    with settings_tabs[1]:
        st.markdown("#### Build Defaults")
        st.selectbox("Default Machine", configurations["machines"] if configurations["machines"] else ["None"], index=0)
        st.selectbox("Default Distro", configurations["distros"] if configurations["distros"] else ["None"], index=0)
        st.number_input("Default Parallel Jobs", min_value=1, max_value=16, value=4)
    
    with settings_tabs[2]:
        st.markdown("#### Storage Management")
        st.slider("Maximum Build History Entries", 10, 100, 50)
        st.toggle("Auto-clean Old Builds", value=False)
        st.number_input("Keep builds for (days)", min_value=1, max_value=365, value=30)
    
    st.button("Save Settings", type="primary", disabled=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Footer with credits and version
footer_html = """
<div style="margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #e0e0e0; text-align: center;">
    <p>
        <span style="font-weight: bold;">Embedded Linux Builder</span> | 
        <span style="color: #666;">Version 1.0.0</span> | 
        <span style="color: #666;">© 2025 Your Company</span>
    </p>
</div>
"""

st.markdown(footer_html, unsafe_allow_html=True)