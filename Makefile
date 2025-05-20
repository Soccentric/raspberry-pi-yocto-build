# Include .env file if it exists
-include .env

# Docker image to use for building
DOCKER_IMAGE ?= image_jetson
# KAS configuration file
KAS_FILE ?= kas/kas-poky-jetson.yml
# Default target
DEFAULT_TARGET ?= core-image-minimal
# Directory to mount inside docker container
WORKDIR ?= /workdir

# Current directory
CURDIR := $(shell pwd)

.PHONY: build clean shell help sdk esdk copy-sdk copy-esdk

help:
	@echo "Yocto build system with KAS"
	@echo ""
	@echo "Usage:"
	@echo "  make build         Build the default image ($(DEFAULT_TARGET))"
	@echo "  make build TARGET=<target>  Build a specific target"
	@echo "  make sdk           Build the SDK for the default image"
	@echo "  make sdk TARGET=<target>  Build SDK for a specific target"
	@echo "  make copy-sdk      Copy built SDK files to /work/docker/sdk"
	@echo "  make esdk          Build the extensible SDK for the default image"
	@echo "  make esdk TARGET=<target>  Build extensible SDK for a specific target"
	@echo "  make copy-esdk     Copy built eSDK files to /work/docker/esdk"
	@echo "  make clean         Clean the build"
	@echo "  make shell         Open a shell in the build environment"
	@echo ""
	@echo "Environment variables (can be set in .env file):"
	@echo "  DOCKER_IMAGE       Docker image to use (default: $(DOCKER_IMAGE))"
	@echo "  KAS_FILE           KAS configuration file (default: $(KAS_FILE))"
	@echo "  DEFAULT_TARGET     Default build target (default: $(DEFAULT_TARGET))"

build:
	@echo "Building Yocto using KAS with $(DOCKER_IMAGE)"
	docker run --rm -it \
		-v $(CURDIR):$(WORKDIR) \
		-v ~/.ssh:/home/$$(id -un)/.ssh \
		-v ~/.gitconfig:/home/$$(id -un)/.gitconfig \
		--user $$(id -u):$$(id -g) \
		$(DOCKER_IMAGE) \
		kas build $(KAS_FILE) $(if $(TARGET),:$(TARGET),)

clean:
	@echo "Cleaning build directory"
	docker run --rm -it \
		-v $(CURDIR):$(WORKDIR) \
		--user $$(id -u):$$(id -g) \
		$(DOCKER_IMAGE) \
		kas shell --command "rm -rf build/tmp" $(KAS_FILE)

shell:
	@echo "Opening a shell in the build environment"
	docker run --rm -it \
		-v $(CURDIR):$(WORKDIR) \
		-v ~/.ssh:/home/$$(id -un)/.ssh \
		-v ~/.gitconfig:/home/$$(id -un)/.gitconfig \
		--user $$(id -u):$$(id -g) \
		$(DOCKER_IMAGE) \
		kas shell $(KAS_FILE)

sdk:
	@echo "Building SDK for $(if $(TARGET),$(TARGET),$(DEFAULT_TARGET))"
	docker run --rm -it \
		-v $(CURDIR):$(WORKDIR) \
		-v ~/.ssh:/home/$$(id -un)/.ssh \
		-v ~/.gitconfig:/home/$$(id -un)/.gitconfig \
		--user $$(id -u):$$(id -g) \
		$(DOCKER_IMAGE) \
		kas shell --command "bitbake $(if $(TARGET),$(TARGET),$(DEFAULT_TARGET)) -c populate_sdk" $(KAS_FILE)
	@echo "SDK build completed. Run 'make copy-sdk' to copy files to /work/docker/sdk"

copy-sdk: sdk 
	@echo "Copying SDK to docker/sdk directory"
	@mkdir -p docker/sdk
	@if [ -n "$$(find $(CURDIR)/build/tmp/deploy/sdk -name '*.sh' 2>/dev/null)" ]; then \
		SDK_FILE=$$(find $(CURDIR)/build/tmp/deploy/sdk -name '*.sh' | head -1); \
		cp -v $$SDK_FILE docker/sdk/sdk.sh; \
		echo "SDK file copied and renamed to docker/sdk/sdk.sh"; \
	else \
		echo "No SDK files found to copy"; \
	fi

esdk:
	@echo "Building extensible SDK for $(if $(TARGET),$(TARGET),$(DEFAULT_TARGET))"
	docker run --rm -it \
		-v $(CURDIR):$(WORKDIR) \
		-v ~/.ssh:/home/$$(id -un)/.ssh \
		-v ~/.gitconfig:/home/$$(id -un)/.gitconfig \
		--user $$(id -u):$$(id -g) \
		$(DOCKER_IMAGE) \
		kas shell --command "bitbake $(if $(TARGET),$(TARGET),$(DEFAULT_TARGET)) -c populate_sdk_ext" $(KAS_FILE)
	@echo "eSDK build completed. Run 'make copy-esdk' to copy files to /work/docker/esdk"

copy-esdk: esdk
	@echo "Copying extensible SDK to docker/esdk directory"
	@mkdir -p docker/esdk
	@if [ -n "$$(find $(CURDIR)/build/tmp/deploy/sdk -name '*-toolchain-ext-*.sh' 2>/dev/null)" ]; then \
		ESDK_FILE=$$(find $(CURDIR)/build/tmp/deploy/sdk -name '*-toolchain-ext-*.sh' | head -1); \
		cp -v $$ESDK_FILE docker/esdk/esdk.sh; \
		echo "eSDK file copied and renamed to docker/esdk/esdk.sh"; \
	else \
		echo "No eSDK files found to copy"; \
	fi
