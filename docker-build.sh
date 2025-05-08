#!/bin/bash
set -e

# This script runs the build process in a Docker container
# to ensure a consistent build environment

# Configuration
IMAGE_NAME="kas-container"
DOCKER_IMAGE="ghcr.io/siemens/kas/kas:latest"

# Parse arguments
KAS_MACHINE=${KAS_MACHINE:-raspberrypi4}
KAS_DISTRO=${KAS_DISTRO:-poky}
KAS_IMAGE=${KAS_IMAGE:-core-image-base}
KAS_FILE=${KAS_FILE:-kas/kas-poky-jetson.yml}

# Usage info
usage() {
  echo "Usage: $0 [options]"
  echo ""
  echo "Options:"
  echo "  -m MACHINE  Set the machine (default: $KAS_MACHINE)"
  echo "  -d DISTRO   Set the distro (default: $KAS_DISTRO)"
  echo "  -i IMAGE    Set the image type (default: $KAS_IMAGE)"
  echo "  -f FILE     Set the KAS file (default: $KAS_FILE)"
  echo "  -h          Display this help message"
  exit 1
}

# Parse command-line options
while getopts "m:d:i:f:h" opt; do
  case $opt in
    m)
      KAS_MACHINE=$OPTARG
      ;;
    d)
      KAS_DISTRO=$OPTARG
      ;;
    i)
      KAS_IMAGE=$OPTARG
      ;;
    f)
      KAS_FILE=$OPTARG
      ;;
    h)
      usage
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      usage
      ;;
  esac
done

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not found. Please install Docker and try again."
    exit 1
fi

echo "🚀 Starting Docker-based build with:"
echo "  Machine: $KAS_MACHINE"
echo "  Distribution: $KAS_DISTRO"
echo "  Image: $KAS_IMAGE"
echo "  Configuration: $KAS_FILE"
echo ""

# Set environment variables for the build
export KAS_MACHINE
export KAS_DISTRO
export KAS_IMAGE

# Run KAS in Docker
docker run -it --rm \
  -v $(pwd):/work \
  -e KAS_MACHINE \
  -e KAS_DISTRO \
  -e KAS_IMAGE \
  --workdir=/work \
  $DOCKER_IMAGE \
  build $KAS_FILE

echo "✅ Build completed!"
