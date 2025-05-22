SHELL := /bin/bash
.SHELLFLAGS := -ec -o pipefail

# Load configuration variables from .env file
-include .env

# Configuration variables with defaults if not in .env
KAS_FILE ?= kas/kas-poky-jetson.yml
KAS_MACHINE = raspberrypi5
KAS_DISTRO ?= poky
KAS_IMAGE ?= core-image-base
KAS_REPOS_FILE ?= common.yml
KAS_LOCAL_CONF_FILE ?= local.yml
KAS_BBLAYERS_FILE ?= bblayers.yml

# Docker configuration
DOCKER_IMAGE_PRIMARY ?= image_rpi
DOCKER_IMAGE_FALLBACK ?= image-rpi
DOCKER_WORKDIR ?= /work
DOCKER_USER ?= $(shell id -u):$(shell id -g)

# Determine which Docker image to use
DOCKER_IMAGE := $(shell if docker image inspect $(DOCKER_IMAGE_PRIMARY) >/dev/null 2>&1; then echo $(DOCKER_IMAGE_PRIMARY); elif docker image inspect $(DOCKER_IMAGE_FALLBACK) >/dev/null 2>&1; then echo $(DOCKER_IMAGE_FALLBACK); else echo $(DOCKER_IMAGE_PRIMARY); fi)

# Commands
KAS_CMD := docker run --rm -it \
	-v $(PWD):$(DOCKER_WORKDIR) \
	-v ~/.ssh:/home/build/.ssh \
	-v /etc/localtime:/etc/localtime:ro \
	--user $(DOCKER_USER) \
	--workdir $(DOCKER_WORKDIR) \
	$(DOCKER_IMAGE) kas
RM := rm
MKDIR := mkdir -p
CP := cp -v
DATE := $(shell date +%Y-%m-%d_%H-%M-%S)
ARTIFACTS_DIR := artifacts/$(DATE)

.PHONY: all build menu shell clean help status list-images flash info sdk esdk copy-artifacts cleanall cleansstate cleandownloads cleanmachine clean-artifacts build-with-progress docker-build

# Export variables so that included kas files can access them
export KAS_MACHINE KAS_DISTRO KAS_IMAGE KAS_REPOS_FILE KAS_LOCAL_CONF_FILE KAS_BBLAYERS_FILE

# Default target is build, which uses Docker
all: help 

# Check if Docker image exists
check-docker-image:
	@echo "Checking for Docker image '$(DOCKER_IMAGE)'..."
	@if ! docker image inspect $(DOCKER_IMAGE) >/dev/null 2>&1; then \
		echo "Docker image '$(DOCKER_IMAGE)' not found locally."; \
		echo "Checking for fallback image '$(DOCKER_IMAGE_FALLBACK)'..."; \
		if ! docker image inspect $(DOCKER_IMAGE_FALLBACK) >/dev/null 2>&1; then \
			echo "Fallback image not found either. Attempting to pull $(DOCKER_IMAGE_PRIMARY)..."; \
			if ! docker pull $(DOCKER_IMAGE_PRIMARY); then \
				echo "Could not pull $(DOCKER_IMAGE_PRIMARY). Trying $(DOCKER_IMAGE_FALLBACK)..."; \
				if ! docker pull $(DOCKER_IMAGE_FALLBACK); then \
					echo "Error: Failed to pull either Docker image."; \
					echo "Please create a valid Docker image for KAS."; \
					exit 1; \
				fi; \
				echo "Using $(DOCKER_IMAGE_FALLBACK) as Docker image."; \
				DOCKER_IMAGE=$(DOCKER_IMAGE_FALLBACK); \
			else \
				echo "Using $(DOCKER_IMAGE_PRIMARY) as Docker image."; \
				DOCKER_IMAGE=$(DOCKER_IMAGE_PRIMARY); \
			fi; \
		else \
			echo "Using $(DOCKER_IMAGE_FALLBACK) as Docker image."; \
			DOCKER_IMAGE=$(DOCKER_IMAGE_FALLBACK); \
		fi; \
	else \
		echo "Using $(DOCKER_IMAGE) as Docker image."; \
	fi

# Build the image defined in the KAS_FILE always using Docker
build: check-docker-image
	@echo "Starting Docker build using $(DOCKER_IMAGE)..."
	$(KAS_CMD) build $(KAS_FILE)
	@$(MAKE) copy-artifacts

# Build the SDK for the specified image (using Docker)
sdk: check-docker-image
	$(KAS_CMD) shell $(KAS_FILE) -c "bitbake -c populate_sdk $(KAS_IMAGE)"
	@$(MAKE) copy-artifacts SDK=1

# Build the extensible SDK for the specified image
esdk: check-docker-image
	$(KAS_CMD) shell $(KAS_FILE) -c "bitbake -c populate_sdk_ext $(KAS_IMAGE)"
	@$(MAKE) copy-artifacts ESDK=1

# Launch the bitbake terminal UI for the configuration in KAS_FILE
menu: check-docker-image
	$(KAS_CMD) shell $(KAS_FILE) -c "bitbake -u ncurses $(KAS_IMAGE)"

# Enter the KAS shell environment for the configuration in KAS_FILE
shell: check-docker-image
	$(KAS_CMD) shell $(KAS_FILE)

# Clean the build output using bitbake
clean: check-docker-image
	$(KAS_CMD) shell $(KAS_FILE) -c "bitbake -c clean $(KAS_IMAGE)"
	@echo "Basic clean completed for $(KAS_IMAGE)"

# Clean all build output including tmp directory
cleanall: check-docker-image
	$(KAS_CMD) shell $(KAS_FILE) -c "rm -rf tmp"
	@echo "Complete build directory cleaned"

# Clean the shared state cache
cleansstate: check-docker-image
	$(KAS_CMD) shell $(KAS_FILE) -c "bitbake -c cleansstate $(KAS_IMAGE)"
	@echo "Sstate cache cleaned for $(KAS_IMAGE)"

# Clean the downloads directory
cleandownloads: check-docker-image
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
	@if [ ! -f "$(IMAGE)" ]; then \
		echo "Error: Image file $(IMAGE) not found"; \
		exit 1; \
	fi
	@if [ ! -b "$(DEVICE)" ]; then \
		echo "Error: $(DEVICE) is not a valid block device"; \
		exit 1; \
	fi
	@echo "WARNING: This will overwrite all data on $(DEVICE). Are you sure? (y/N)"
	@read -r CONFIRM && [ "$$CONFIRM" = "y" ] || exit 1
	@echo "Flashing image to $(DEVICE) at $$(date '+%Y-%m-%d %H:%M:%S')"
	sudo dd if=$(IMAGE) of=$(DEVICE) bs=4M status=progress conv=fsync
	@echo "Image flashed successfully to $(DEVICE)"
	@if command -v cmp >/dev/null; then \
		echo "Verifying image..."; \
		sudo cmp --silent $(IMAGE) $(DEVICE) || echo "WARNING: Verification failed, image may not be flashed correctly"; \
	fi

# Copy built artifacts to dated artifacts directory
copy-artifacts:
	@echo "Copying artifacts to $(ARTIFACTS_DIR)..."
	@$(MKDIR) $(ARTIFACTS_DIR)
	@if [ -d "build/tmp/deploy/images/$(KAS_MACHINE)" ]; then \
		echo "Copying image files..."; \
		$(MKDIR) $(ARTIFACTS_DIR)/images; \
		$(CP) build/tmp/deploy/images/$(KAS_MACHINE)/*.wic $(ARTIFACTS_DIR)/images/ 2>/dev/null || true; \
		$(CP) build/tmp/deploy/images/$(KAS_MACHINE)/*.rpi-sdimg $(ARTIFACTS_DIR)/images/ 2>/dev/null || true; \
		$(CP) build/tmp/deploy/images/$(KAS_MACHINE)/*.sdimg $(ARTIFACTS_DIR)/images/ 2>/dev/null || true; \
	fi
	@if [ "$(SDK)" = "1" ] && [ -d "build/tmp/deploy/sdk" ]; then \
		echo "Copying SDK files..."; \
		$(MKDIR) $(ARTIFACTS_DIR)/sdk; \
		$(CP) build/tmp/deploy/sdk/*.sh $(ARTIFACTS_DIR)/sdk/ 2>/dev/null || true; \
	fi
	@if [ "$(ESDK)" = "1" ] && [ -d "build/tmp/deploy/sdk" ]; then \
		echo "Copying extensible SDK files..."; \
		$(MKDIR) $(ARTIFACTS_DIR)/esdk; \
		$(CP) build/tmp/deploy/sdk/*-toolchain-ext-*.sh $(ARTIFACTS_DIR)/esdk/ 2>/dev/null || true; \
	fi
	@rm -f artifacts/latest
	@ln -sf $(DATE) artifacts/latest
	@echo "Artifacts copied to $(ARTIFACTS_DIR)"

# Clean up old artifacts (keeps the latest N directories)
clean-artifacts:
	@echo "Cleaning old artifacts..."
	@if [ -z "$(KEEP)" ]; then \
		echo "Please specify how many artifact directories to keep with KEEP=N"; \
		echo "Example: make clean-artifacts KEEP=5"; \
		exit 1; \
	fi
	@if [ ! -d "artifacts" ]; then \
		echo "No artifacts directory found."; \
		exit 0; \
	fi
	@if [ $$(find artifacts -maxdepth 1 -type d | wc -l) -le $$(( $(KEEP) + 1 )) ]; then \
		echo "There are fewer than $(KEEP) artifact directories. Nothing to clean."; \
		exit 0; \
	fi
	@ls -td artifacts/20* | tail -n +$$(( $(KEEP) + 1 )) | xargs rm -rf
	@echo "Kept the $(KEEP) most recent artifact directories."

# Show build info with more details
info:
	@echo "Build environment information:"
	@echo "  KAS using Docker image: $(DOCKER_IMAGE)"
	@echo "  Docker version: $$(docker --version)"
	@echo "  Docker installed: $$(command -v docker >/dev/null && echo 'Yes' || echo 'No')"
	@echo "  Available disk space: $$(df -h . | awk 'NR==2 {print $$4}')"
	@echo "  Memory: $$(free -h | awk '/^Mem:/ {print $$2}')"
	@echo "  CPU cores: $$(nproc)"
	@echo "  Kernel: $$(uname -r)"
	@echo "  Build host: $$(hostname)"
	@echo ""
	@echo "Configuration:"
	@echo "  KAS_FILE: $(KAS_FILE)"
	@echo "  KAS_MACHINE: $(KAS_MACHINE)"
	@echo "  KAS_DISTRO: $(KAS_DISTRO)"
	@echo "  KAS_IMAGE: $(KAS_IMAGE)"
	@echo ""
	@echo "Artifacts:"
	@if [ -d "artifacts" ]; then \
		echo "  Latest build: $$(readlink -f artifacts/latest 2>/dev/null || echo 'None')"; \
		echo "  Total artifact directories: $$(find artifacts -maxdepth 1 -type d | wc -l)"; \
		echo "  Disk space used by artifacts: $$(du -sh artifacts | cut -f1)"; \
	else \
		echo "  No artifacts directory found."; \
	fi

# Show progress of long-running operations
build-with-progress:
	@$(MKDIR) artifacts
	@$(MAKE) build 2>&1 | tee artifacts/build-$(DATE).log & \
	PID=$$!; \
	echo "Build started with PID: $$PID"; \
	while kill -0 $$PID 2>/dev/null; do \
		echo "Build in progress... $$(date '+%Y-%m-%d %H:%M:%S')"; \
		sleep 60; \
	done; \
	wait $$PID

# Display help with added commands
help:
	@echo "Makefile for Yocto/KAS Embedded Linux Builder"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  all            Default target, builds the image using Docker."
	@echo "  build          Build the image defined in the KAS_FILE using Docker and copy to artifacts."
	@echo "  build-with-progress Build with progress display every minute using Docker."
	@echo "  sdk            Build the SDK for the specified image and copy to artifacts."
	@echo "  esdk           Build the extensible SDK (eSDK) for the specified image and copy to artifacts."
	@echo "  copy-artifacts Copy built images/SDKs to date-stamped artifacts directory (use COMPRESS=1 to compress)."
	@echo "  clean-artifacts Clean old artifact directories (specify KEEP=N to keep N most recent directories)."
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
	@echo "  DOCKER_IMAGE         Docker image to use (default: $(DOCKER_IMAGE))"
	@echo "  DOCKER_WORKDIR       Working directory in Docker container (default: $(DOCKER_WORKDIR))"

.DEFAULT_GOAL := all