# Makefile for Docker and Docker Compose commands

# Use host user/group IDs for container permissions (inherited from parent Makefile or set here)
USER_ID ?= $(shell id -u)
GROUP_ID ?= $(shell id -g)

.PHONY: build up down ps logs shell clean

# Build the Docker image
build:
	USER_ID=$(USER_ID) GROUP_ID=$(GROUP_ID) docker-compose build

# Start containers
up:
	USER_ID=$(USER_ID) GROUP_ID=$(GROUP_ID) docker-compose up -d

# Stop containers
down:
	docker-compose down

# Show running containers
ps:
	docker-compose ps

# Show container logs
logs:
	docker-compose logs

# Open a shell in the rpi container
shell:
	docker-compose exec rpi bash

# Clean up Docker resources
clean:
	docker-compose down --rmi all --volumes --remove-orphans

# Help command
help:
	@echo "Available commands:"
	@echo "  make build    - Build Docker image"
	@echo "  make up       - Start containers"
	@echo "  make down     - Stop containers"
	@echo "  make ps       - List running containers"
	@echo "  make logs     - Show container logs"
	@echo "  make shell    - Open shell in rpi container"
	@echo "  make clean    - Clean up Docker resources"
