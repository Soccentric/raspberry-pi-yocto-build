# Master Makefile for Jetson Docker project
# Coordinates builds and operations across all subprojects: edk, image, and sdk

# Define directories
DIRS := esdk image sdk jenkins

.PHONY: all build up down ps logs shell clean help $(DIRS)

# Default target: build all components
all: help 

# Build all Docker images
build:
	@echo "=== Building all Docker images ==="
	@for dir in $(DIRS); do \
		echo "Building in $$dir..."; \
		$(MAKE) -C $$dir build; \
	done
	@echo "=== All Docker images built successfully ==="

# Start all containers
up:
	@echo "=== Starting all containers ==="
	@for dir in $(DIRS); do \
		echo "Starting containers in $$dir..."; \
		$(MAKE) -C $$dir up; \
	done
	@echo "=== All containers started ==="

# Stop all containers
down:
	@echo "=== Stopping all containers ==="
	@for dir in $(DIRS); do \
		echo "Stopping containers in $$dir..."; \
		$(MAKE) -C $$dir down; \
	done
	@echo "=== All containers stopped ==="

# Show all running containers
ps:
	@echo "=== Listing all running containers ==="
	@for dir in $(DIRS); do \
		echo "Containers in $$dir:"; \
		$(MAKE) -C $$dir ps; \
	done

# Show all container logs
logs:
	@echo "=== Showing all container logs ==="
	@for dir in $(DIRS); do \
		echo "Logs from $$dir:"; \
		$(MAKE) -C $$dir logs; \
	done

# Clean up all Docker resources
clean:
	@echo "=== Cleaning all Docker resources ==="
	@for dir in $(DIRS); do \
		echo "Cleaning resources in $$dir..."; \
		$(MAKE) -C $$dir clean; \
	done
	@echo "=== All Docker resources cleaned ==="

# Individual component targets
esdk:
	@echo "=== Building esdk component ==="
	$(MAKE) -C esdk build

image:
	@echo "=== Building image component ==="
	$(MAKE) -C image build

sdk:
	@echo "=== Building sdk component ==="
	$(MAKE) -C sdk build

jenkins:
	@echo "=== Building jenkins component ==="
	$(MAKE) -C jenkins build

# Shell access to specific component (usage: make shell-esdk, make shell-image, make shell-sdk, make shell-jenkins)
shell-%:
	@component=$$(echo $@ | sed 's/shell-//'); \
	echo "Opening shell in $$component"; \
	$(MAKE) -C $$component shell

# Help command
help:
	@echo "Master Makefile for Jetson Docker project"
	@echo ""
	@echo "Available commands:"
	@echo "  make all               - Build all components (default)"
	@echo "  make build             - Build all Docker images"
	@echo "  make up                - Start all containers"
	@echo "  make down              - Stop all containers"
	@echo "  make ps                - List all running containers"
	@echo "  make logs              - Show all container logs"
	@echo "  make clean             - Clean up all Docker resources"
	@echo ""
	@echo "Individual component commands:"
	@echo "  make esdk              - Build only the esdk component"
	@echo "  make image             - Build only the image component"
	@echo "  make sdk               - Build only the sdk component"
	@echo "  make jenkins           - Build only the jenkins component"
	@echo "  make shell-<component> - Open shell in specific component (e.g., make shell-esdk)"
	@echo ""
	@echo "For more specific commands, cd into component directory and run make help"