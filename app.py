import streamlit as st
import subprocess
import os

# Get the absolute path of the directory where app.py is located
# This ensures that 'make' commands are run from the project root.
APP_DIR = os.path.dirname(os.path.abspath(__file__))
MAKEFILE_PATH = os.path.join(APP_DIR, "Makefile")

def run_make_command(command):
    """Runs a make command and streams the output."""
    st.info(f"Running: make {command}")
    progress_bar = st.progress(0)
    output_placeholder = st.empty()
    full_output = []

    try:
        process = subprocess.Popen(
            ["make", command],
            cwd=APP_DIR,
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


st.set_page_config(layout="wide")
st.title("Makefile Command Runner")

st.sidebar.header("Makefile Targets")

# Define Makefile targets
targets = {
    "build": "Build the image defined in the KAS_FILE.",
    "menu": "Launch the KAS menu (Interactive - best run in terminal).",
    "shell": "Enter the KAS shell environment (Interactive - best run in terminal).",
    "clean": "Clean the build output."
}

for target, desc in targets.items():
    if st.sidebar.button(f"Run: make {target}", key=f"run_{target}"):
        st.session_state.current_target = target
        st.session_state.output = "" # Clear previous output
        st.session_state.return_code = None

    if st.session_state.get("current_target") == target:
        st.header(f"Executing: `make {target}`")
        st.caption(desc)
        
        if target in ["menu", "shell"]:
            st.warning(
                f"The `make {target}` command is interactive and may not function as expected in this web UI. "
                f"It's recommended to run this command directly in your terminal in the directory: `{APP_DIR}`"
            )
            # Optionally, you could attempt to run it and display whatever output it might produce,
            # but it's unlikely to be a good user experience.
            # For now, we'll just show the warning.
            if st.button(f"Proceed with 'make {target}' anyway (not recommended)", key=f"proceed_{target}"):
                 with st.spinner(f"Attempting to run 'make {target}'..."):
                    output, rc = run_make_command(target)
                    st.session_state.output = output
                    st.session_state.return_code = rc
        else:
            with st.spinner(f"Executing 'make {target}'..."):
                output, rc = run_make_command(target)
                st.session_state.output = output
                st.session_state.return_code = rc
        
        # Clear the current target so it doesn't re-run on refresh unless button is clicked again
        st.session_state.current_target = None


st.markdown("---")
st.header("Makefile Content")
try:
    with open(MAKEFILE_PATH, "r") as f:
        makefile_content = f.read()
    st.code(makefile_content, language="makefile")
except FileNotFoundError:
    st.error(f"Makefile not found at {MAKEFILE_PATH}")
except Exception as e:
    st.error(f"Could not read Makefile: {e}")

st.sidebar.markdown("---")
st.sidebar.info(
    "Click on a button to execute the corresponding Makefile command. "
    "Output will be displayed on the main page."
)