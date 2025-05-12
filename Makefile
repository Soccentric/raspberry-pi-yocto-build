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

# Docker configuration
DOCKER_IMAGE ?= image_rpi
DOCKER_VOLUME_OPTS ?= -v $(PWD):/work -v $(HOME)/.ssh:/home/build/.ssh:ro
DOCKER_OPTS ?= --rm -it $(DOCKER_VOLUME_OPTS) -w /work
DOCKER_RUN := docker run $(DOCKER_OPTS) $(DOCKER_IMAGE)

# Commands
KAS_CMD := kas
RM := rm
MKDIR := mkdir -p
CP := cp -v
DATE := $(shell date +%Y-%m-%d_%H-%M-%S)
ARTIFACTS_DIR := artifacts/$(DATE)

.PHONY: all build menu shell clean help status list-images flash info sdk esdk copy-artifacts cleanall cleansstate cleandownloads cleanmachine clean-artifacts build-with-progress docker-build docker-shell docker-menu docker-sdk docker-esdk docker-clean docker-check docker-init docker-status docker-list-images docker-info docker-cleanall docker-cleansstate docker-cleandownloads docker-cleanmachine docker-build-with-progress docker-check-config

# Export variables so that included kas files can access them
export KAS_MACHINE KAS_DISTRO KAS_IMAGE KAS_REPOS_FILE KAS_LOCAL_CONF_FILE KAS_BBLAYERS_FILE

# Default target is help (see .DEFAULT_GOAL at the end)
all: docker-check help

# Docker initialization - create the Docker image if it doesn't exist
docker-init:
	@echo "Checking for Docker image $(DOCKER_IMAGE)..."
	@if ! docker image inspect $(DOCKER_IMAGE) >/dev/null 2>&1; then \
		echo "Docker image '$(DOCKER_IMAGE)' not found. Creating it..."; \
		if [ -f "Dockerfile" ]; then \
			docker build -t $(DOCKER_IMAGE) .; \
		else \
			echo "ERROR: Dockerfile not found. Cannot create Docker image."; \
			echo "Please create a Dockerfile or pull an appropriate image and tag it as $(DOCKER_IMAGE)"; \
			exit 1; \
		fi; \
	else \
		echo "Docker image '$(DOCKER_IMAGE)' exists."; \
	fi
	@echo "Ensuring KAS configuration directories exist..."
	@mkdir -p $(dir $(KAS_FILE))
	@if [ ! -f "$(KAS_FILE)" ]; then \
		echo "WARNING: KAS configuration file $(KAS_FILE) does not exist."; \
		echo "You may need to create this file before running a build."; \
	fi

# Build the image defined in the KAS_FILE (using Docker by default)
build: docker-build

# Docker-based build
docker-build: docker-check
	@echo "Checking KAS configuration files..."
	@if [ ! -f "$(KAS_FILE)" ]; then \
		echo "ERROR: KAS configuration file not found: $(KAS_FILE)"; \
		echo "Please check that the KAS_FILE variable is set correctly."; \
		exit 1; \
	fi
	@echo "Using KAS configuration: $(KAS_FILE)"
	@echo "Running build in Docker container..."
	$(DOCKER_RUN) bash -c "$(KAS_CMD) build $(KAS_FILE)"
	@$(MAKE) copy-artifacts

# Add a configuration check target
docker-check-config: docker-check
	@echo "Verifying KAS configuration files..."
	@if [ ! -f "$(KAS_FILE)" ]; then \
		echo "ERROR: KAS configuration file not found: $(KAS_FILE)"; \
		echo "Please check that the KAS_FILE variable is set correctly."; \
		exit 1; \
	fi
	@echo "KAS configuration file exists: $(KAS_FILE)"
	@$(DOCKER_RUN) bash -c "echo 'KAS_FILE: $(KAS_FILE)'; \
		echo 'KAS_MACHINE: $(KAS_MACHINE)'; \
		echo 'Checking KAS environment...'; \
		$(KAS_CMD) --help >/dev/null && echo 'KAS is properly installed.'; \
		echo 'Checking configuration directories...'; \
		ls -la $$(dirname $(KAS_FILE)) || echo 'Warning: Cannot list KAS directory'; \
		echo 'Done checking configuration.'"

# Docker versions of all commands
docker-status: docker-check
	$(DOCKER_RUN) bash -c "echo 'Current configuration:'; \
		echo '  KAS_MACHINE: $(KAS_MACHINE)'; \
		echo '  KAS_DISTRO: $(KAS_DISTRO)'; \
		echo '  KAS_IMAGE: $(KAS_IMAGE)'; \
		echo ''; \
		echo 'Build status:'; \
		if [ -d 'build/tmp/deploy/images/$(KAS_MACHINE)' ]; then \
			echo '  Images built for $(KAS_MACHINE): ' \$$(ls -1 build/tmp/deploy/images/$(KAS_MACHINE)/*.wic 2>/dev/null | wc -l); \
			ls -lh build/tmp/deploy/images/$(KAS_MACHINE)/*.wic 2>/dev/null || echo '  No .wic images found'; \
		else \
			echo '  No images built for $(KAS_MACHINE)'; \
		fi"

docker-list-images: docker-check
	$(DOCKER_RUN) bash -c "echo 'Available images:'; \
		find build/tmp/deploy/images -type f -name '*.wic' -o -name '*.sdimg' -o -name '*.rpi-sdimg' | sort"

docker-cleanmachine: docker-check
	$(DOCKER_RUN) bash -c "rm -rf build/tmp/deploy/images/$(KAS_MACHINE)"
	@echo "Machine output cleaned for $(KAS_MACHINE) using Docker"

docker-cleandownloads: docker-check
	$(DOCKER_RUN) bash -c "$(KAS_CMD) shell $(KAS_FILE) -c \"rm -rf downloads\""
	@echo "Downloads directory cleaned using Docker"

docker-cleansstate: docker-check
	$(DOCKER_RUN) bash -c "$(KAS_CMD) shell $(KAS_FILE) -c \"bitbake -c cleansstate $(KAS_IMAGE)\""
	@echo "Sstate cache cleaned for $(KAS_IMAGE) using Docker"

docker-cleanall: docker-check
	$(DOCKER_RUN) bash -c "$(KAS_CMD) shell $(KAS_FILE) -c \"rm -rf tmp\""
	@echo "Complete build directory cleaned using Docker"

docker-info: docker-check
	$(DOCKER_RUN) bash -c "echo 'Build environment information:'; \
		echo '  KAS version: ' \$$(kas --version); \
		echo '  Available disk space: ' \$$(df -h /work | awk 'NR==2 {print \$$4}'); \
		echo '  Memory: ' \$$(free -h | awk '/^Mem:/ {print \$$2}'); \
		echo '  CPU cores: ' \$$(nproc); \
		echo '  Kernel: ' \$$(uname -r); \
		echo '  Build container: ' \$$(hostname); \
		echo ''; \
		echo 'Configuration:'; \
		echo '  KAS_FILE: $(KAS_FILE)'; \
		echo '  KAS_MACHINE: $(KAS_MACHINE)'; \
		echo '  KAS_DISTRO: $(KAS_DISTRO)'; \
		echo '  KAS_IMAGE: $(KAS_IMAGE)'; \
		echo ''; \
		echo 'Artifacts:'; \
		if [ -d 'artifacts' ]; then \
			echo '  Latest build: ' \$$(readlink -f artifacts/latest 2>/dev/null || echo 'None'); \
			echo '  Total artifact directories: ' \$$(find artifacts -maxdepth 1 -type d | wc -l); \
			echo '  Disk space used by artifacts: ' \$$(du -sh artifacts | cut -f1); \
		else \
			echo '  No artifacts directory found.'; \
		fi"

docker-build-with-progress: docker-check
	@$(MKDIR) artifacts
	@$(MAKE) docker-build 2>&1 | tee artifacts/build-$(DATE).log & \
	PID=$$!; \
	echo "Docker build started with PID: $$PID"; \
	while kill -0 $$PID 2>/dev/null; do \
		echo "Docker build in progress... $$(date '+%Y-%m-%d %H:%M:%S')"; \
		sleep 60; \
	done; \
	wait $$PID

# Default to Docker versions
status: docker-status
list-images: docker-list-images
cleanmachine: docker-cleanmachine
cleandownloads: docker-cleandownloads
cleansstate: docker-cleansstate
cleanall: docker-cleanall
info: docker-info
build-with-progress: docker-build-with-progress

# Display help with added commands and Docker emphasis
help:
	@echo "Makefile for Yocto/KAS Embedded Linux Docker Builder"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Docker is the primary build method used by this Makefile."
	@echo ""
	@echo "Initial Setup:"
	@echo "  docker-init     Initialize Docker environment and build the image if needed"
	@echo "  docker-check    Check if Docker is available and the specified image exists"
	@echo ""
	@echo "Primary Build Targets:"
	@echo "  build           Build the image using Docker (default method)"
	@echo "  docker-build    Explicitly build the image using Docker"
	@echo "  sdk             Build the SDK using Docker"
	@echo "  docker-sdk      Explicitly build the SDK using Docker"
	@echo "  esdk            Build the extensible SDK using Docker"
	@echo "  docker-esdk     Explicitly build the extensible SDK using Docker"
	@echo ""
	@echo "Environment Access:"
	@echo "  shell           Enter the KAS shell environment using Docker"
	@echo "  docker-shell    Explicitly enter the KAS shell using Docker"
	@echo "  menu            Launch the BitBake ncurses UI using Docker"
	@echo "  docker-menu     Explicitly launch the BitBake ncurses UI using Docker"
	@echo ""
	@echo "Cleaning Targets:"
	@echo "  clean           Clean build output using Docker"
	@echo "  docker-clean    Explicitly clean build output using Docker"
	@echo "  cleanall        Clean the entire tmp directory using Docker"
	@echo "  docker-cleanall Explicitly clean the entire tmp directory using Docker"
	@echo "  cleansstate     Clean the shared state cache using Docker"
	@echo "  docker-cleansstate Explicitly clean the shared state cache using Docker"
	@echo "  cleandownloads  Clean the downloads directory using Docker"
	@echo "  docker-cleandownloads Explicitly clean the downloads directory using Docker"
	@echo "  cleanmachine    Clean specific machine output using Docker"
	@echo "  docker-cleanmachine Explicitly clean specific machine output using Docker"
	@echo ""
	@echo "Information and Status:"
	@echo "  status          Show build status using Docker"
	@echo "  docker-status   Explicitly show build status using Docker"
	@echo "  list-images     List all built images using Docker"
	@echo "  docker-list-images Explicitly list all built images using Docker" 
	@echo "  info            Show build environment information using Docker"
	@echo "  docker-info     Explicitly show build environment information using Docker"
	@echo ""
	@echo "Artifact Management:"
	@echo "  copy-artifacts  Copy built images/SDKs to date-stamped artifacts directory (use COMPRESS=1 to compress)"
	@echo "  clean-artifacts Clean old artifact directories (specify KEEP=N to keep N most recent directories)"
	@echo ""
	@echo "Deployment:"
	@echo "  flash           Flash an image to an SD card (DEVICE and IMAGE parameters required)"
	@echo ""
	@echo "Progress Monitoring:"
	@echo "  build-with-progress      Build with progress updates using Docker"
	@echo "  docker-build-with-progress Explicitly build with progress updates using Docker"
	@echo ""
	@echo "Configuration Variables:"
	@echo "  KAS_FILE             Path to the KAS configuration file (default: $(KAS_FILE))"
	@echo "  KAS_MACHINE          Target machine (default: $(KAS_MACHINE))"
	@echo "  KAS_DISTRO           Target distribution (default: $(KAS_DISTRO))"
	@echo "  KAS_IMAGE            Target image type (default: $(KAS_IMAGE))"
	@echo "  DOCKER_IMAGE         Docker image to use for builds (default: $(DOCKER_IMAGE))"
	@echo "  DOCKER_OPTS          Additional Docker options (default: $(DOCKER_OPTS))"
	@echo "  DOCKER_VOLUME_OPTS   Volume mapping options (default: maps current dir to /work)"

.DEFAULT_GOAL := help