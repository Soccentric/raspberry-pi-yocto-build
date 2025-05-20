# Makefile for Docker and Docker Compose commands

.PHONY: build up down ps logs shell clean

# Build the Docker image
build:
	docker-compose build

# Start containers
up:
	docker-compose up -d

# Stop containers
down:
	docker-compose down

# Show running containers
ps:
	docker-compose ps

# Show container logs
logs:
	docker-compose logs

# Open a shell in the jetson container
shell:
	docker-compose exec jetson bash

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
	@echo "  make shell    - Open shell in jetson container"
	@echo "  make clean    - Clean up Docker resources"
