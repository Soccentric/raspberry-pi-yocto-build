#!/bin/bash

#===============================================================================
# QEMU Emulation Launch Script for Yocto-built Images
#===============================================================================
# Description:
#   This script launches QEMU to emulate Yocto-built images for x86_64 architecture.
#   It handles dependencies, configuration options, and provides a flexible
#   interface for testing Yocto builds without physical hardware.
#
# Author: Sandesh Ghimire
# Version: 1.0.1
# Date: Updated $(date +%Y-%m-%d)
#
# Usage Examples:
#   Basic usage:
#     ./run_qemu.sh
#
#   Specify custom kernel and rootfs:
#     ./run_qemu.sh -k custom-kernel.bin -r custom-rootfs.ext4
#
#   Allocate more resources:
#     ./run_qemu.sh -m 4G -c 8
#
#   Disable networking:
#     ./run_qemu.sh --network no
#
# Notes:
#   - KVM acceleration will significantly improve performance if available
#   - For remote debugging, consider adding GDB server options
#   - Root password for default Yocto images is typically empty
#===============================================================================

# Default configuration
KERNEL_IMAGE="bzImage"
ROOTFS_IMAGE="core-image-minimal-qemux86-64.ext4"
MEMORY="1G"                # Memory allocated to the virtual machine
SMP="4"                    # Number of CPU cores
ENABLE_KVM="auto"          # auto: use if available, yes: require it, no: disable
ENABLE_NETWORK="yes"       # Enable virtual networking

# Help function - Displays usage information
show_help() {
    echo "======================================================================"
    echo "                QEMU Launcher for Yocto-built Images"
    echo "======================================================================"
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -k, --kernel IMAGE     Kernel image file (default: $KERNEL_IMAGE)"
    echo "                         Example: -k path/to/bzImage"
    echo ""
    echo "  -r, --rootfs IMAGE     Root filesystem image (default: $ROOTFS_IMAGE)"
    echo "                         Example: -r path/to/rootfs.ext4"
    echo ""
    echo "  -m, --memory SIZE      Memory size with suffix K,M,G (default: $MEMORY)"
    echo "                         Example: -m 2G"
    echo ""
    echo "  -c, --cpu-cores NUM    Number of CPU cores (default: $SMP)"
    echo "                         Example: -c 2"
    echo ""
    echo "  --kvm [auto|yes|no]    KVM acceleration (default: $ENABLE_KVM)"
    echo "                         auto: use if available"
    echo "                         yes:  require KVM (fail if not available)"
    echo "                         no:   disable KVM"
    echo ""
    echo "  --network [yes|no]     Enable networking (default: $ENABLE_NETWORK)"
    echo "                         Example: --network no"
    echo ""
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Troubleshooting:"
    echo "  - If the script fails to start QEMU, ensure QEMU is installed"
    echo "  - For KVM acceleration, ensure /dev/kvm exists and is accessible"
    echo "  - If networking fails, check your firewall settings"
    echo "  - Default root login has no password for most Yocto images"
    echo "======================================================================"
    exit 0
}

# Process command line arguments
# Parses all provided command-line options and sets corresponding variables
while [[ $# -gt 0 ]]; do
    case $1 in
        -k|--kernel)
            KERNEL_IMAGE="$2"
            shift 2
            ;;
        -r|--rootfs)
            ROOTFS_IMAGE="$2"
            shift 2
            ;;
        -m|--memory)
            MEMORY="$2"
            shift 2
            ;;
        -c|--cpu-cores)
            SMP="$2"
            shift 2
            ;;
        --kvm)
            ENABLE_KVM="$2"
            shift 2
            ;;
        --network)
            ENABLE_NETWORK="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            ;;
    esac
done

# Check for required dependencies
echo "========== Environment Setup =========="
echo "Checking QEMU installation..."
if ! command -v qemu-system-x86_64 &> /dev/null; then
    echo "QEMU is not installed. Installing required packages..."
    sudo apt update || { echo "Failed to update package list!"; exit 1; }
    sudo apt install -y qemu-system qemu-utils || { echo "Failed to install QEMU!"; exit 1; }
    echo "QEMU installation completed successfully."
else
    echo "QEMU is already installed: $(qemu-system-x86_64 --version | head -n1)"
fi

# Verify image files exist
echo "========== Verifying Image Files =========="
echo "Looking for kernel image: $KERNEL_IMAGE"
if [ ! -f "$KERNEL_IMAGE" ]; then
    echo "Error: Kernel image '$KERNEL_IMAGE' not found!"
    echo "Hint: Make sure you're running this script from the directory containing your images,"
    echo "      or specify the correct path with -k option."
    exit 1
else
    echo "✓ Kernel image found: $(ls -lh "$KERNEL_IMAGE" | awk '{print $5}')"
fi

echo "Looking for rootfs image: $ROOTFS_IMAGE"
if [ ! -f "$ROOTFS_IMAGE" ]; then
    echo "Error: Root filesystem image '$ROOTFS_IMAGE' not found!"
    echo "Hint: Make sure you're running this script from the directory containing your images,"
    echo "      or specify the correct path with -r option."
    exit 1
else
    echo "✓ Root filesystem found: $(ls -lh "$ROOTFS_IMAGE" | awk '{print $5}')"
fi

# Configure QEMU options
echo "========== Configuring QEMU =========="

# Basic system configuration
QEMU_OPTS="-kernel $KERNEL_IMAGE"
QEMU_OPTS+=" -drive file=$ROOTFS_IMAGE,format=raw"
QEMU_OPTS+=" -append \"root=/dev/sda rw console=ttyS0\""
QEMU_OPTS+=" -nographic"  # Run in terminal, no GUI
QEMU_OPTS+=" -m $MEMORY"  # Memory allocation
QEMU_OPTS+=" -smp $SMP"   # CPU cores

# Configure KVM acceleration if available and requested
# KVM provides near-native performance by utilizing CPU virtualization extensions
echo "Checking KVM availability..."
if [ "$ENABLE_KVM" = "auto" ] || [ "$ENABLE_KVM" = "yes" ]; then
    if [ -e /dev/kvm ] && [ -r /dev/kvm ] && [ -w /dev/kvm ]; then
        QEMU_OPTS+=" -enable-kvm"
        echo "✓ KVM acceleration enabled (performance will be significantly better)"
        echo "  KVM device: $(ls -la /dev/kvm)"
    elif [ "$ENABLE_KVM" = "yes" ]; then
        echo "⚠ Warning: KVM was explicitly requested but is not available!"
        echo "  Check that:"
        echo "    1. Your CPU supports virtualization (Intel VT-x/AMD-V)"
        echo "    2. Virtualization is enabled in BIOS/UEFI"
        echo "    3. The kvm kernel module is loaded (try: 'modprobe kvm_intel' or 'modprobe kvm_amd')"
        echo "    4. You have permissions to access /dev/kvm"
        exit 1
    else
        echo "ℹ KVM not available. Emulation will be slower."
    fi
else
    echo "ℹ KVM disabled by configuration. Emulation will be slower."
fi

# Configure networking
# This creates a virtual network interface in the guest with NAT to host network
if [ "$ENABLE_NETWORK" = "yes" ]; then
    QEMU_OPTS+=" -netdev user,id=net0,hostfwd=tcp::2222-:22 -device virtio-net-pci,netdev=net0"
    echo "✓ Networking enabled"
    echo "  SSH forwarding: Connect with 'ssh -p 2222 root@localhost' when VM is running"
else
    echo "ℹ Networking disabled by configuration"
fi

# Launch QEMU
echo "========== QEMU Launch Summary =========="
echo "Starting QEMU with the following configuration:"
echo "  Kernel: $KERNEL_IMAGE"
echo "  Rootfs: $ROOTFS_IMAGE"
echo "  Memory: $MEMORY"
echo "  CPUs: $SMP"
echo ""
echo "Control commands while running:"
echo "  • Exit QEMU: Press Ctrl+A, then X"
echo "  • Get QEMU console: Press Ctrl+A, then C"
echo ""
echo "Launching QEMU..."
echo "========== QEMU Console Output =========="
eval "qemu-system-x86_64 $QEMU_OPTS"

# Script exit handling
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "========== Troubleshooting =========="
    echo "QEMU exited with code $EXIT_CODE."
    echo "Common issues:"
    echo "  • If you see 'Could not initialize KVM', try running with '--kvm no'"
    echo "  • If network setup failed, try running with '--network no'"
    echo "  • If kernel boot fails, ensure the kernel and rootfs are compatible"
    echo "  • For permission errors, make sure you have rights to access the image files"
    echo ""
    echo "For more help, check QEMU documentation: https://www.qemu.org/docs/master/"
fi

exit $EXIT_CODE
