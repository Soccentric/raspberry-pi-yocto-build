import subprocess
import threading
import streamlit as st
from datetime import datetime
import re
import time

def _execute_command_worker(command_name, args_list, command_key):
    st.session_state[f"{command_key}_is_running"] = True
    st.session_state[f"{command_key}_start_time"] = datetime.now()
    st.session_state[f"{command_key}_output_live_html"] = "<div style=\"color: #4CAF50;\">▶ Starting build process...</div>\n"
    st.session_state[f"{command_key}_output_full_text"] = ""
    st.session_state[f"{command_key}_stderr_text"] = ""
    st.session_state[f"{command_key}_progress_value"] = 0.0
    st.session_state[f"{command_key}_status_message"] = "Build in progress..."
    st.session_state[f"{command_key}_status_type"] = "info" # info, success, error, warning
    st.session_state[f"{command_key}_return_code"] = None

    cmd_to_run = ["make", command_name]
    if args_list:
        cmd_to_run.extend(args_list)
    
    st.session_state[f"{command_key}_executed_command_str"] = ' '.join(cmd_to_run)

    process = subprocess.Popen(cmd_to_run, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True)
    
    live_text_html = "<div style=\"color: #4CAF50;\">▶ Starting build process...</div>\n"
    estimated_tasks = 100 
    current_task = 0

    for line in process.stdout:
        st.session_state[f"{command_key}_output_full_text"] += line
        
        styled_line = line.strip()
        
        if "NOTE: Tasks" in line and "Summary:" in line:
            match = re.search(r"NOTE: Tasks:.*?(\d+)\s*total", line) # Adjusted regex
            if match:
                new_estimated_tasks = int(match.group(1))
                if new_estimated_tasks > 0 : # Avoid division by zero or nonsensical updates
                    estimated_tasks = new_estimated_tasks
                    current_task = 0 # Reset task count if new summary found
                    st.session_state[f"{command_key}_progress_value"] = 0.05
        elif "NOTE: Task " in line and " done" in line: # Simpler match for "done"
            current_task += 1
            if estimated_tasks > 0:
                progress = min(0.95, current_task / estimated_tasks) # Cap at 95% until truly done
                st.session_state[f"{command_key}_progress_value"] = progress
                st.session_state[f"{command_key}_status_message"] = f"Building: {current_task}/{estimated_tasks} tasks ({int(progress*100)}%)"
                st.session_state[f"{command_key}_status_type"] = "info"
        
        if "ERROR" in styled_line or "error:" in styled_line.lower():
            styled_line = f"<div style=\"color: #FF5252;\">{styled_line}</div>" # Red for errors
            st.session_state[f"{command_key}_status_message"] = "⚠️ Errors detected in build"
            st.session_state[f"{command_key}_status_type"] = "error"
        elif "WARNING" in styled_line or "warning:" in styled_line.lower():
            styled_line = f"<div style=\"color: #FFC107;\">{styled_line}</div>" # Yellow for warnings
            if st.session_state[f"{command_key}_status_type"] != "error": # Don't overwrite error status
                st.session_state[f"{command_key}_status_message"] = "⚠️ Warnings detected"
                st.session_state[f"{command_key}_status_type"] = "warning"
        elif "NOTE: recipe " in styled_line and ": completed" in styled_line:
             styled_line = f"<div style=\"color: #4CAF50;\">{styled_line}</div>" # Green for success notes
        elif styled_line.startswith("NOTE: Running task"):
            styled_line = f"<div style=\"color: #2196F3;\">➤ {styled_line}</div>" # Blue for running tasks
        else:
            styled_line = f"<div>{styled_line}</div>"
            
        if styled_line.strip() != "<div></div>":
            live_text_html += styled_line + "\n"
            st.session_state[f"{command_key}_output_live_html"] = live_text_html
        
        time.sleep(0.01) # Small delay to allow UI to refresh if main thread is rerunning

    # Capture any remaining stderr
    _, stderr_data = process.communicate()
    st.session_state[f"{command_key}_stderr_text"] = stderr_data
    st.session_state[f"{command_key}_return_code"] = process.returncode
    st.session_state[f"{command_key}_progress_value"] = 1.0 # Mark as 100%

    end_time = datetime.now()
    duration = (end_time - st.session_state[f"{command_key}_start_time"]).seconds

    if process.returncode == 0:
        st.session_state[f"{command_key}_status_message"] = f"✅ Command completed successfully in {duration}s"
        st.session_state[f"{command_key}_status_type"] = "success"
        live_text_html += f"<div style=\"color: #4CAF50;\">✅ Build completed successfully in {duration}s</div>\n"
    else:
        st.session_state[f"{command_key}_status_message"] = f"❌ Command failed (code {process.returncode}) after {duration}s"
        st.session_state[f"{command_key}_status_type"] = "error"
        live_text_html += f"<div style=\"color: #FF5252;\">❌ Build failed (code {process.returncode}) after {duration}s</div>\n"
    
    st.session_state[f"{command_key}_output_live_html"] = live_text_html
    st.session_state[f"{command_key}_is_running"] = False

    # Prepare log entry for the main thread to pick up
    log_entry = {
        'command': st.session_state[f"{command_key}_executed_command_str"],
        'timestamp': st.session_state[f"{command_key}_start_time"].strftime('%Y-%m-%d %H:%M:%S'),
        'output': st.session_state[f"{command_key}_output_full_text"],
        'stderr': stderr_data,
        'success': process.returncode == 0,
        'has_warning': "WARNING" in st.session_state[f"{command_key}_output_full_text"] or "warning:" in st.session_state[f"{command_key}_output_full_text"].lower(),
        'duration': f"{duration}s"
    }
    if 'completed_logs_buffer' not in st.session_state:
        st.session_state.completed_logs_buffer = []
    st.session_state.completed_logs_buffer.append(log_entry)


def start_make_command(command_name, args_list=None, command_key="current_command_op"):
    # Ensure no other command is running with this key, or handle appropriately
    if st.session_state.get(f"{command_key}_is_running", False):
        st.warning(f"Another operation ('{st.session_state.get(f'{command_key}_executed_command_str', 'previous')}') is already in progress.")
        return

    # Initialize/reset state for this command key
    st.session_state[f"{command_key}_is_running"] = True
    st.session_state[f"{command_key}_command_name_display"] = command_name # For display purposes
    st.session_state.active_command_key = command_key # Mark this key as the one to display

    thread = threading.Thread(target=_execute_command_worker, args=(command_name, args_list, command_key))
    thread.daemon = True 
    thread.start()
    st.experimental_rerun() # Rerun to start showing progress immediately

