SHELL := /bin/bash
.SHELLFLAGS := -ec -o pipefail

# Configuration variables
KAS_FILE ?= kas/kas-poky-jetson.yml
KAS_MACHINE ?= raspberrypi4
KAS_DISTRO ?= poky
KAS_IMAGE ?= core-image-base
KAS_REPOS_FILE ?= common.yml
KAS_LOCAL_CONF_FILE ?= local.yml
KAS_BBLAYERS_FILE ?= bblayers.yml

# Commands
KAS_CMD := kas
RM := rm
MKDIR := mkdir -p

.PHONY: all build menu shell clean help status list-images flash info

# Export variables so that included kas files can access them
export KAS_MACHINE KAS_DISTRO KAS_IMAGE KAS_REPOS_FILE KAS_LOCAL_CONF_FILE KAS_BBLAYERS_FILE

# Default target is help (see .DEFAULT_GOAL at the end)
all: help

# Build the image defined in the KAS_FILE
build:
	$(KAS_CMD) build $(KAS_FILE)

# Launch the KAS menu for the configuration in KAS_FILE
menu:
	$(KAS_CMD) menu $(KAS_FILE)

# Enter the KAS shell environment for the configuration in KAS_FILE
shell:
	$(KAS_CMD) shell $(KAS_FILE)

# Clean the build output
clean:
	$(RM) -rf build/tmp # Adjust this path if your TMPDIR is different
	$(RM) -rf build/sstate-cache # Adjust if your SSTATE_DIR is different

# Clean only specific machine output
cleanmachine:
	$(RM) -rf build/tmp/deploy/images/$(KAS_MACHINE)

# Show build status
status:
	@echo "Current configuration:"
	@echo "  KAS_MACHINE: $(KAS_MACHINE)"
	@echo "  KAS_DISTRO: $(KAS_DISTRO)"
	@echo "  KAS_IMAGE: $(KAS_IMAGE)"
	@echo ""
	@echo "Build status:"
	@if [ -d "build/tmp/deploy/images/$(KAS_MACHINE)" ]; then \
		echo "  Images built for $(KAS_MACHINE): $$(ls -1 build/tmp/deploy/images/$(KAS_MACHINE)/*.wic 2>/dev/null | wc -l)"; \
		ls -lh build/tmp/deploy/images/$(KAS_MACHINE)/*.wic 2>/dev/null || echo "  No .wic images found"; \
	else \
		echo "  No images built for $(KAS_MACHINE)"; \
	fi

# List built images
list-images:
	@echo "Available images:"
	@find build/tmp/deploy/images -type f -name "*.wic" -o -name "*.sdimg" -o -name "*.rpi-sdimg" | sort

# Flash an image to an SD card (USE WITH CAUTION)
# Usage: make flash DEVICE=/dev/sdX IMAGE=path/to/image.wic
flash:
	@if [ -z "$(DEVICE)" ]; then \
		echo "Error: DEVICE parameter required. Usage: make flash DEVICE=/dev/sdX IMAGE=path/to/image.wic"; \
		exit 1; \
	fi
	@if [ -z "$(IMAGE)" ]; then \
		echo "Error: IMAGE parameter required. Usage: make flash DEVICE=/dev/sdX IMAGE=path/to/image.wic"; \
		exit 1; \
	fi
	@echo "WARNING: This will overwrite all data on $(DEVICE). Are you sure? (y/N)"
	@read -r CONFIRM && [ "$$CONFIRM" = "y" ] || exit 1
	sudo dd if=$(IMAGE) of=$(DEVICE) bs=4M status=progress && sync
	@echo "Image flashed successfully to $(DEVICE)"

# Show build info
info:
	@echo "Build environment information:"
	@echo "  KAS version: $$(kas --version)"
	@echo "  Docker installed: $$(command -v docker >/dev/null && echo 'Yes' || echo 'No')"
	@echo "  Available disk space: $$(df -h . | awk 'NR==2 {print $$4}')"
	@echo "  Memory: $$(free -h | awk '/^Mem:/ {print $$2}')"
	@echo ""
	@echo "Configuration:"
	@echo "  KAS_FILE: $(KAS_FILE)"
	@echo "  KAS_MACHINE: $(KAS_MACHINE)"
	@echo "  KAS_DISTRO: $(KAS_DISTRO)"
	@echo "  KAS_IMAGE: $(KAS_IMAGE)"

# Display help
help:
	@echo "Makefile for Yocto/KAS Embedded Linux Builder"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  all            Default target, displays this help message."
	@echo "  build          Build the image defined in the KAS_FILE."
	@echo "  menu           Launch the KAS menu for the configuration in KAS_FILE."
	@echo "  shell          Enter the KAS shell environment for the configuration in KAS_FILE."
	@echo "  clean          Clean all build output (build/tmp and build/sstate-cache)."
	@echo "  cleanmachine   Clean only specific machine output."
	@echo "  status         Show the current build status and configuration."
	@echo "  list-images    List all built images."
	@echo "  flash          Flash an image to an SD card (DEVICE and IMAGE parameters required)."
	@echo "  info           Show build environment information."
	@echo "  help           Display this help message."
	@echo ""
	@echo "Configuration Variables:"
	@echo "  KAS_FILE             Path to the KAS configuration file (default: $(KAS_FILE))"
	@echo "  KAS_MACHINE          Target machine (default: $(KAS_MACHINE))"
	@echo "  KAS_DISTRO           Target distribution (default: $(KAS_DISTRO))"
	@echo "  KAS_IMAGE            Target image type (default: $(KAS_IMAGE))"
	@echo "  KAS_REPOS_FILE       Repository definitions file (default: $(KAS_REPOS_FILE))"
	@echo "  KAS_LOCAL_CONF_FILE  Local configuration file (default: $(KAS_LOCAL_CONF_FILE))"
	@echo "  KAS_BBLAYERS_FILE    BitBake layers file (default: $(KAS_BBLAYERS_FILE))"

.DEFAULT_GOAL := help