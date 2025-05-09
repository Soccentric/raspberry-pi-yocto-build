import streamlit as st
from datetime import datetime
import time  # For the rerun loop

from utils import read_env_file, save_env_file, get_makefile_options, get_build_info_raw
from ui_tabs import render_build_operations_tab, render_system_management_tab, render_image_tools_tab, render_build_logs_tab
# command_executor is used by ui_tabs

# Initialize session state for build logs if not present
if 'build_logs' not in st.session_state:
    st.session_state.build_logs = []
if 'active_command_key' not in st.session_state:
    st.session_state.active_command_key = None
if 'completed_logs_buffer' not in st.session_state:
    st.session_state.completed_logs_buffer = []

# Set page configuration
st.set_page_config(
    page_title="Yocto/KAS Builder",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("Yocto/KAS Builder Interface")
    
    makefile_defaults, _ = get_makefile_options()
    current_env_values = read_env_file()
    
    # Combine defaults with current env, current_env takes precedence
    # Only for display and saving, actual build uses .env file directly
    config_display = {key: current_env_values.get(key, makefile_defaults.get(key, "")) for key in ["KAS_MACHINE", "KAS_DISTRO", "KAS_IMAGE"]}

    with st.sidebar:
        st.header("Configuration")
        st.caption("Set build parameters (saved to .env)")
        
        kas_machine = st.text_input("Machine", value=config_display.get("KAS_MACHINE", ""))
        kas_distro = st.text_input("Distribution", value=config_display.get("KAS_DISTRO", ""))
        kas_image = st.text_input("Image", value=config_display.get("KAS_IMAGE", ""))
        
        if st.button("Save Configuration"):
            env_to_save = read_env_file()  # Start with all existing .env values
            # Update with values from sidebar
            env_to_save["KAS_MACHINE"] = kas_machine
            env_to_save["KAS_DISTRO"] = kas_distro
            env_to_save["KAS_IMAGE"] = kas_image
            
            # Ensure other KAS variables from defaults are present if not already in .env
            for key in ["KAS_FILE", "KAS_REPOS_FILE", "KAS_LOCAL_CONF_FILE", "KAS_BBLAYERS_FILE"]:
                if key not in env_to_save and key in makefile_defaults:
                    env_to_save[key] = makefile_defaults[key]
            save_env_file(env_to_save)
            st.experimental_rerun()  # To reflect saved changes if any
            
        st.divider()
        st.header("Environment Info")
        if st.button("Show Build Info (make info)"):
            # This is a quick command, can be run directly or threaded for consistency
            # For now, displaying its output directly without full threaded UI
            info_output = get_build_info_raw()
            st.text_area("Build Info Output", info_output, height=200)

    # Display area for running command output (if any)
    active_key = st.session_state.get("active_command_key", None)
    if active_key and st.session_state.get(f"{active_key}_is_running", False):
        st.subheader(f"Running: `{st.session_state.get(f'{active_key}_executed_command_str', 'make ...')}`")
        start_time_obj = st.session_state.get(f"{active_key}_start_time")
        if start_time_obj:
            st.caption(f"Started at {start_time_obj.strftime('%H:%M:%S')}")

        progress_val = st.session_state.get(f"{active_key}_progress_value", 0.0)
        status_msg = st.session_state.get(f"{active_key}_status_message", "Initializing...")
        status_type = st.session_state.get(f"{active_key}_status_type", "info")

        st.progress(progress_val)
        if status_type == "info": st.info(status_msg)
        elif status_type == "success": st.success(status_msg)  # Should only show on completion
        elif status_type == "error": st.error(status_msg)
        elif status_type == "warning": st.warning(status_msg)
        
        st.markdown("<h4 style='margin-bottom: 0px; padding-bottom: 0px;'>Live Console Output:</h4>", unsafe_allow_html=True)
        live_html = st.session_state.get(f"{active_key}_output_live_html", "<div>Waiting for output...</div>")
        st.markdown(f"""
            <div style="background-color: #0E1117; border-radius: 5px; padding: 10px; margin-top: 0px; height: 300px; overflow-y: auto; font-family: monospace; white-space: pre-wrap;">
                {live_html}
            </div>
            """, unsafe_allow_html=True)
        
        stderr_txt = st.session_state.get(f"{active_key}_stderr_text", "")
        if stderr_txt:
            st.error("Standard Error Output:")
            st.code(stderr_txt, language="bash")
        
        # Auto-refresh loop
        time.sleep(0.5)  # Adjust refresh rate as needed
        st.experimental_rerun()

    elif active_key and not st.session_state.get(f"{active_key}_is_running", True) and st.session_state.get(f"{active_key}_return_code") is not None:
        # Command has finished, display final message and process logs
        st.success(f"Operation `{st.session_state.get(f'{active_key}_executed_command_str', 'make ...')}` finished.")
        
        # Process logs from buffer
        if st.session_state.completed_logs_buffer:
            for log_entry in st.session_state.completed_logs_buffer:
                st.session_state.build_logs.insert(0, log_entry)
            st.session_state.build_logs = st.session_state.build_logs[:10]  # Keep last 10
            st.session_state.completed_logs_buffer = []

        # Display final status from the command execution
        final_status_msg = st.session_state.get(f"{active_key}_status_message", "Operation complete.")
        final_status_type = st.session_state.get(f"{active_key}_status_type", "info")
        if final_status_type == "success": st.success(final_status_msg)
        elif final_status_type == "error": st.error(final_status_msg)
        else: st.info(final_status_msg)
        
        stderr_txt = st.session_state.get(f"{active_key}_stderr_text", "")
        if stderr_txt:  # Show stderr again if it was part of a failure
            st.error("Final Standard Error Output:")
            st.code(stderr_txt, language="bash")

        with st.expander("View Full Output for Completed Command"):
            st.text_area("Full Output", st.session_state.get(f"{active_key}_output_full_text", "No full output recorded."), height=300)

        st.session_state.active_command_key = None  # Reset for next command
        st.experimental_rerun()  # Rerun once to clear the running display and update logs tab

    # Tabs for operations
    tab_titles = ["Build Operations", "System Management", "Image Tools", "Build Logs"]
    tab1, tab2, tab3, tab4 = st.tabs(tab_titles)
    
    with tab1:
        render_build_operations_tab()
    with tab2:
        render_system_management_tab(config_display)  # Pass config if needed by tab
    with tab3:
        render_image_tools_tab()
    with tab4:
        render_build_logs_tab()

if __name__ == "__main__":
    main()
