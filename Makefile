SHELL := /bin/bash
.SHELLFLAGS := -ec -o pipefail

# Load configuration variables from .env file
-include .env

# Configuration variables with defaults if not in .env
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
CP := cp -v
DATE := $(shell date +%Y-%m-%d_%H-%M-%S)
ARTIFACTS_DIR := artifacts/$(DATE)

.PHONY: all build menu shell clean help status list-images flash info sdk esdk copy-artifacts cleanall cleansstate cleandownloads cleanmachine

# Export variables so that included kas files can access them
export KAS_MACHINE KAS_DISTRO KAS_IMAGE KAS_REPOS_FILE KAS_LOCAL_CONF_FILE KAS_BBLAYERS_FILE

# Default target is help (see .DEFAULT_GOAL at the end)
all: help

# Build the image defined in the KAS_FILE
build:
	$(KAS_CMD) build $(KAS_FILE)
	@$(MAKE) copy-artifacts

# Build the SDK for the specified image
sdk:
	$(KAS_CMD) shell $(KAS_FILE) -c "bitbake -c populate_sdk $(KAS_IMAGE)"
	@$(MAKE) copy-artifacts SDK=1

# Build the extensible SDK for the specified image
esdk:
	$(KAS_CMD) shell $(KAS_FILE) -c "bitbake -c populate_sdk_ext $(KAS_IMAGE)"
	@$(MAKE) copy-artifacts ESDK=1

# Launch the bitbake terminal UI for the configuration in KAS_FILE
menu:
	$(KAS_CMD) shell $(KAS_FILE) -c "bitbake -u ncurses $(KAS_IMAGE)"

# Enter the KAS shell environment for the configuration in KAS_FILE
shell:
	$(KAS_CMD) shell $(KAS_FILE)

# Clean the build output using bitbake
clean:
	$(KAS_CMD) shell $(KAS_FILE) -c "bitbake -c clean $(KAS_IMAGE)"
	@echo "Basic clean completed for $(KAS_IMAGE)"

# Clean all build output including tmp directory
cleanall:
	$(KAS_CMD) shell $(KAS_FILE) -c "rm -rf tmp"
	@echo "Complete build directory cleaned"

# Clean the shared state cache
cleansstate:
	$(KAS_CMD) shell $(KAS_FILE) -c "bitbake -c cleansstate $(KAS_IMAGE)"
	@echo "Sstate cache cleaned for $(KAS_IMAGE)"

# Clean the downloads directory
cleandownloads:
	$(KAS_CMD) shell $(KAS_FILE) -c "rm -rf downloads"
	@echo "Downloads directory cleaned"

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

# Copy built artifacts to dated artifacts directory
copy-artifacts:
	@$(MKDIR) $(ARTIFACTS_DIR)/images
	@echo "Copying artifacts to $(ARTIFACTS_DIR)"
	@if [ ! -d "build/tmp/deploy/images/$(KAS_MACHINE)" ]; then \
		echo "ERROR: No build artifacts directory found at build/tmp/deploy/images/$(KAS_MACHINE)"; \
		echo "  Have you run 'make build' first to build the images?"; \
		exit 1; \
	fi
	@echo "Looking for images in build/tmp/deploy/images/$(KAS_MACHINE)..."
	@if find build/tmp/deploy/images/$(KAS_MACHINE) -type f -name "*.wic" -o -name "*.sdimg" -o -name "*.rpi-sdimg" | grep -q .; then \
		find build/tmp/deploy/images/$(KAS_MACHINE) -type f -name "*.wic" -o -name "*.sdimg" -o -name "*.rpi-sdimg" | \
		xargs -I{} $(CP) {} $(ARTIFACTS_DIR)/images/; \
		echo "Image files copied successfully."; \
	else \
		echo "WARNING: No image artifacts (*.wic, *.sdimg, *.rpi-sdimg) found to copy"; \
		echo "  Have you completed a build using 'make build' that produced image files?"; \
		echo "  Current machine: $(KAS_MACHINE)"; \
		echo "  Current image: $(KAS_IMAGE)"; \
	fi
	@if [ "$(SDK)" = "1" -o "$(ESDK)" = "1" ]; then \
		$(MKDIR) $(ARTIFACTS_DIR)/sdk; \
		if [ ! -d "build/tmp/deploy/sdk" ]; then \
			echo "WARNING: SDK directory not found at build/tmp/deploy/sdk"; \
		elif find build/tmp/deploy/sdk -type f -name "*.sh" | grep -q .; then \
			find build/tmp/deploy/sdk -type f -name "*.sh" | \
			xargs -I{} $(CP) {} $(ARTIFACTS_DIR)/sdk/; \
			echo "SDK files copied successfully."; \
		else \
			echo "WARNING: No SDK artifacts (*.sh) found to copy"; \
		fi \
	fi
	@echo "Artifacts copied to $(ARTIFACTS_DIR)"
	@echo "Creating latest symlink"
	@rm -f artifacts/latest
	@ln -sf $(DATE) artifacts/latest

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
	@echo "  build          Build the image defined in the KAS_FILE and copy to artifacts."
	@echo "  sdk            Build the SDK for the specified image and copy to artifacts."
	@echo "  esdk           Build the extensible SDK (eSDK) for the specified image and copy to artifacts."
	@echo "  copy-artifacts Copy built images/SDKs to date-stamped artifacts directory."
	@echo "  menu           Launch the BitBake ncurses (terminal) UI for interactive build."
	@echo "  shell          Enter the KAS shell environment for the configuration in KAS_FILE."
	@echo "  clean          Clean build output for the specified image using BitBake."
	@echo "  cleanall       Clean the entire tmp directory for a complete rebuild."
	@echo "  cleansstate    Clean the shared state cache for the specified image."
	@echo "  cleandownloads Clean the downloads directory."
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