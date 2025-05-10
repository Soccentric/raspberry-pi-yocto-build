# Makefile for Docker and Docker Compose commands

.PHONY: build up down ps logs shell clean jupyter

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

# Open a shell in the rpi container
shell:
	docker-compose exec rpi bash

# Clean up Docker resources
clean:
	docker-compose down --rmi all --volumes --remove-orphans

# Start Jupyter Notebook server
jupyter:
	docker-compose exec rpi jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root

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
	@echo "  make jupyter  - Start Jupyter Notebook server"
