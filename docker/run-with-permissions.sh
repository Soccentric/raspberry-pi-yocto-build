#!/bin/bash
# Script to run docker-compose with host user's UID and GID for permissions sync

# Get the current user and group IDs
export USER_ID=$(id -u)
export GROUP_ID=$(id -g)

# Echo the values for verification
echo "Using USER_ID=$USER_ID and GROUP_ID=$GROUP_ID for Docker container"

# Change to the directory specified as the first argument
if [ $# -ge 1 ]; then
    cd "$1" || { echo "Error: Directory $1 not found"; exit 1; }
    shift
else
    echo "Usage: $0 <directory> [docker-compose command]"
    echo "Example: $0 edk up -d"
    echo "Example: $0 sdk build --no-cache"
    exit 1
fi

# Run docker-compose with the passed arguments, or default to "up -d"
if [ $# -eq 0 ]; then
    echo "Running: docker-compose up -d"
    docker-compose up -d
else
    echo "Running: docker-compose $*"
    docker-compose "$@"
fi
