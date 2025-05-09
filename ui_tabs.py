import streamlit as st
from command_executor import start_make_command
from utils import list_available_images, get_build_status # Assuming kas_machine is read from config for cleanmachine

def display_build_logs_history():
    if 'build_logs' not in st.session_state or not st.session_state.build_logs:
        st.info("No build logs yet.")
        return
    
    st.markdown("### Build History")
    for i, log in enumerate(st.session_state.build_logs):
        icon = "✅" if log['success'] else ("⚠️" if log.get('has_warning') else "❌")
        with st.expander(f"{icon} {log['command']} - {log['timestamp']} ({log['duration']})"):
            st.markdown(f"**Status:** {'Success' if log['success'] else 'Failed'}")
            st.text_area("Full Output", log['output'], height=300, key=f"log_out_{i}")
            if log['stderr']:
                st.error("Error Output:")
                st.code(log['stderr'], language="bash")

def render_build_operations_tab():
    st.header("Build Operations")
    
    st.subheader("Build Image / SDK")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Build Image", key="build_image_btn", use_container_width=True):
            start_make_command("build", command_key="build_op")
    with col2:
        if st.button("Build SDK", key="build_sdk_btn", use_container_width=True):
            start_make_command("sdk", command_key="sdk_op")
    with col3:
        if st.button("Build eSDK", key="build_esdk_btn", use_container_width=True):
            start_make_command("esdk", command_key="esdk_op")
    
    st.header("Build Status")
    if st.button("Check Status", key="status_btn"):
        # This is a quick operation, so direct execution is fine, or thread it for consistency
        # For now, direct:
        status_output = get_build_status()
        st.text_area("Current Status", status_output, height=200, disabled=True)

def render_system_management_tab(current_config): # Pass current_config for kas_machine if needed
    st.header("System Management")
    
    st.subheader("Clean Operations")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Clean", use_container_width=True, key="clean_btn"):
            start_make_command("clean", command_key="clean_op")
    with col2:
        if st.button("Clean All", use_container_width=True, key="cleanall_btn"):
            # Confirmation for destructive actions should ideally be handled before starting the command
            # For simplicity, we assume user is cautious or add a checkbox here.
            start_make_command("cleanall", command_key="cleanall_op")
    with col3:
        if st.button("Clean SState", use_container_width=True, key="cleansstate_btn"):
            start_make_command("cleansstate", command_key="cleansstate_op")
    with col4:
        if st.button("Clean Downloads", use_container_width=True, key="cleandownloads_btn"):
            start_make_command("cleandownloads", command_key="cleandownloads_op")
            
    st.subheader("Clean Machine Output")
    if st.button("Clean Machine Output", use_container_width=False, key="cleanmachine_btn"):
        # The Makefile uses KAS_MACHINE from env, so direct call is fine.
        start_make_command("cleanmachine", command_key="cleanmachine_op")
            
    st.subheader("Artifacts Management")
    if st.button("Copy Artifacts to Dated Directory", use_container_width=False, key="copyartifacts_btn"):
        start_make_command("copy-artifacts", command_key="copyartifacts_op")

def render_image_tools_tab():
    st.header("Image Tools")
    
    st.subheader("Available Images")
    if st.button("List Available Images", key="listimages_btn"):
        images = list_available_images()
        if images:
            for img in images:
                st.code(img)
        else:
            st.info("No images found or error listing images.")
    
    st.subheader("Flash Image to SD Card")
    st.warning("⚠️ Flashing will overwrite all data on the selected device!")
    
    device = st.text_input("Target Device (e.g., /dev/sdX)", key="flash_device_input")
    image_path = st.text_input("Image Path (full path to .wic/.sdimg)", key="flash_image_path_input")
    
    if st.button("Flash Image", use_container_width=True, key="flash_btn"):
        if not device or not image_path:
            st.error("Both device and image path are required!")
        else:
            # Confirmation for flash is handled by Makefile's interactive prompt
            # Pass DEVICE and IMAGE as arguments for 'make flash'
            start_make_command("flash", args_list=[f"DEVICE={device}", f"IMAGE={image_path}"], command_key="flash_op")

def render_build_logs_tab():
    st.header("Build Logs and History")
    # Options for log view (can be re-added if needed)
    # col1, col2 = st.columns(2)
    # with col1:
    #     st.checkbox("Auto-scroll logs", value=True, key="auto_scroll_logs") # This is now implicit
    # with col2:
    #     st.checkbox("Show timestamps in live log", value=True, key="show_timestamps_log") # Timestamps are part of log lines

    display_build_logs_history()
    
    if st.button("Clear Log History", key="clearloghistory_btn"):
        if 'build_logs' in st.session_state:
            st.session_state.build_logs = []
            st.success("Log history cleared!")
            st.experimental_rerun()
