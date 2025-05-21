#!/bin/bash 


SDK="poky-glibc-x86_64-core-image-base-cortexa76-raspberrypi5-toolchain-ext-5.2.sh"
ESDK="poky-glibc-x86_64-core-image-base-cortexa76-raspberrypi5-toolchain-ext-5.2.sh"


CUR_DIR=$(pwd)

DOCKER_DIR="$CUR_DIR/docker"
SDK_DOCKER_DIR="$DOCKER_DIR/sdk"
ESDK_DOCKER_DIR="$DOCKER_DIR/esdk"

SDK_DIR="$CUR_DIR/build/tmp/deploy/sdk/"

# Check if the SDK directory exists
if [ ! -d "$SDK_DIR" ]; then
    echo "SDK directory does not exist: $SDK_DIR"
    exit 1
fi

# Check if the SDK directory is empty
if [ -z "$(ls -A "$SDK_DIR")" ]; then
    echo "SDK directory is empty: $SDK_DIR"
    exit 1
fi

# Create directories for SDK and ESDK
if [ ! -d "$SDK_DOCKER_DIR" ]; then
    mkdir -p "$SDK_DOCKER_DIR"
fi

if [ ! -d "$ESDK_DOCKER_DIR" ]; then
    mkdir -p "$ESDK_DOCKER_DIR"
fi

# Copy SDK and ESDK to their respective directories with new names
cp "$SDK_DIR/$SDK" "$SDK_DOCKER_DIR/sdk.sh"
cp "$SDK_DIR/$ESDK" "$ESDK_DOCKER_DIR/esdk.sh"
echo "SDK copied to $SDK_DOCKER_DIR/sdk.sh"
echo "ESDK copied to $ESDK_DOCKER_DIR/esdk.sh"

# Check if the SDK file exists
if [ ! -f "$SDK_DOCKER_DIR/sdk.sh" ]; then
    echo "SDK file does not exist: $SDK_DOCKER_DIR/sdk.sh"
    exit 1
fi

# Check if the SDK file is empty
if [ ! -s "$SDK_DOCKER_DIR/sdk.sh" ]; then
    echo "SDK file is empty: $SDK_DOCKER_DIR/sdk.sh"
    exit 1
fi

# Check if the ESDK file exists
if [ ! -f "$ESDK_DOCKER_DIR/esdk.sh" ]; then
    echo "ESDK file does not exist: $ESDK_DOCKER_DIR/esdk.sh"
    exit 1
fi

# Check if the ESDK file is empty
if [ ! -s "$ESDK_DOCKER_DIR/esdk.sh" ]; then
    echo "ESDK file is empty: $ESDK_DOCKER_DIR/esdk.sh"
    exit 1
fi

