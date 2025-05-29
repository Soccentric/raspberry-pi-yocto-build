#!/bin/bash

# Full build script for Raspberry Pi Yocto build
# Author: Enhanced by Copilot
# Date: $(date '+%Y-%m-%d')

# Set strict error handling
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Initialize variables
START_TIME=$(date +%s)

# Function to display timestamps in logs
log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${BLUE}[${timestamp}]${NC} $1"
}

# Function to handle errors
error_handler() {
    local line=$1
    local command=$2
    local code=$3
    log "${RED}Error on line $line: Command '$command' exited with status $code${NC}"
    exit $code
}

# Set up error trap
trap 'error_handler ${LINENO} "$BASH_COMMAND" $?' ERR

# Arrays to store step information for table display
STEP_NAMES=()
STEP_TIMES=()
STEP_SECONDS=()

# Function to track step timing
start_step() {
    STEP_NAME="$1"
    STEP_START_TIME=$(date +%s)
    log "${YELLOW}Starting: ${STEP_NAME}${NC}"
}

end_step() {
    local end_time=$(date +%s)
    local elapsed=$((end_time - STEP_START_TIME))
    local hours=$((elapsed / 3600))
    local minutes=$(( (elapsed % 3600) / 60 ))
    local seconds=$((elapsed % 60))
    
    local time_string="${hours}h ${minutes}m ${seconds}s"
    log "${GREEN}Completed: ${STEP_NAME} in ${time_string}${NC}"
    
    # Store data for table
    STEP_NAMES+=("${STEP_NAME}")
    STEP_TIMES+=("${time_string}")
    STEP_SECONDS+=($elapsed)
}

# Function to display a formatted table
display_timing_table() {
    local divider="+---------------------------------+---------------+------------+"
    echo -e "\n${YELLOW}Build Steps Timing Summary:${NC}"
    echo -e "$divider"
    printf "| %-31s | %-13s | %-10s |\n" "Build Step" "Time" "% of Total"
    echo -e "$divider"
    
    local total_seconds=$((END_TIME - START_TIME))
    
    for i in "${!STEP_NAMES[@]}"; do
        local percentage=$(awk "BEGIN {printf \"%.1f\", (${STEP_SECONDS[$i]} / $total_seconds) * 100}")
        printf "| %-31s | %-13s | %10s%% |\n" "${STEP_NAMES[$i]}" "${STEP_TIMES[$i]}" "$percentage"
    done
    
    echo -e "$divider"
    printf "| %-31s | %-13s | %10s%% |\n" "TOTAL" "${HOURS}h ${MINUTES}m ${SECONDS}s" "100.0"
    echo -e "$divider"
}

# Function to show execution time
show_execution_time() {
    END_TIME=$(date +%s)
    ELAPSED_TIME=$((END_TIME - START_TIME))
    HOURS=$((ELAPSED_TIME / 3600))
    MINUTES=$(( (ELAPSED_TIME % 3600) / 60 ))
    SECONDS=$((ELAPSED_TIME % 60))
    
    log "${GREEN}Total execution time: ${HOURS}h ${MINUTES}m ${SECONDS}s${NC}"
    
    # Display timing table
    display_timing_table
}

# Register exit handler
trap show_execution_time EXIT

# Function to get the git root directory
get_git_root() {
    git rev-parse --show-toplevel 2>/dev/null || {
        log "${RED}Not a git repository. Please run this script from within the git repository.${NC}"
        exit 1
    }
}

# Set the root directory to the git repository root
ROOT_DIR=$(get_git_root)
log "${YELLOW}Using git repository root: ${ROOT_DIR}${NC}"

# Change to the root directory
cd "${ROOT_DIR}" || {
    log "${RED}Failed to change to root directory: ${ROOT_DIR}${NC}"
    exit 1
}

# Step 1: Build docker image for system build
start_step "Step 1: Building docker image for system build"
if cd "${ROOT_DIR}/docker"; then
    log "Changed directory to docker"
    if make image; then
        log "${GREEN}Docker image built successfully${NC}"
    else
        log "${RED}Failed to build docker image${NC}"
        exit 1
    fi
    cd "${ROOT_DIR}"
    log "Changed directory back to project root"
else
    log "${RED}Failed to change directory to docker${NC}"
    exit 1
fi
end_step

# Step 2: Build system image
start_step "Step 2: Building system images"
if make -C "${ROOT_DIR}" build; then
    log "${GREEN}System build completed successfully${NC}"
else
    log "${RED}System build failed${NC}"
    exit 1
fi
end_step

# Build SDK
start_step "Building SDK"
if make -C "${ROOT_DIR}" sdk; then
    log "${GREEN}SDK built successfully${NC}"
else
    log "${RED}SDK build failed${NC}"
    exit 1
fi
end_step

# Build eSDK
start_step "Building eSDK"
if make -C "${ROOT_DIR}" esdk; then
    log "${GREEN}eSDK built successfully${NC}"
else
    log "${RED}eSDK build failed${NC}"
    exit 1
fi
end_step

# Step 3: Copy SDK and eSDK to the docker
start_step "Step 3: Copying SDK and eSDK to docker"
if "${ROOT_DIR}/copy_sdk.sh"; then
    log "${GREEN}Copied SDK and eSDK to docker successfully${NC}"
else
    log "${RED}Failed to copy SDK and eSDK to docker${NC}"
    exit 1
fi
end_step

# Step 4: Build SDK and eSDK in docker
start_step "Step 4: Building SDK and eSDK in docker"
if cd "${ROOT_DIR}/docker"; then
    log "Changed directory to docker"
    
    log "${YELLOW}Building SDK in docker...${NC}"
    if make sdk; then
        log "${GREEN}SDK built in docker successfully${NC}"
    else
        log "${RED}SDK build in docker failed${NC}"
        exit 1
    fi
    
    log "${YELLOW}Building eSDK in docker...${NC}"
    if make esdk; then
        log "${GREEN}eSDK built in docker successfully${NC}"
    else
        log "${RED}eSDK build in docker failed${NC}"
        exit 1
    fi
    
    cd "${ROOT_DIR}"
    log "Changed directory back to project root"
else
    log "${RED}Failed to change directory to docker${NC}"
    exit 1
fi
end_step

log "${GREEN}All build steps completed successfully!${NC}"

