.PHONY: help up down build logs test clean restart

help:
	@echo "Crypto ETL Backend - Make Commands"
	@echo "===================================="
	@echo "make up        - Start all services"
	@echo "make down      - Stop all services"
	@echo "make build     - Build Docker images"
	@echo "make logs      - View logs"
	@echo "make test      - Run tests"
	@echo "make clean     - Clean up containers and volumes"
	@echo "make restart   - Restart all services"

up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build

logs:
	docker-compose logs -f

test:
	docker-compose run backend pytest

clean:
	docker-compose down -v
	docker system prune -f

restart: down up
