.DEFAULT_GOAL := help
REDIS_CONTAINER_NAME="pydantic-aioredis"

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-40s\033[0m %s\n", $$1, $$2}'

setup: setup-test ## Setup a dev environment for working in this repo. Assumes in a venv or other isolation
	pip install -r requirements-dev.txt
	pre-commit install
	pip install -e .

setup-test: ## Setup a testing environment for working in this repo. Assumes in a venv or other isolation
	pip install -r requirements-test.txt

test: setup-test ## run python tests
	pytest

build: setup ## build python packages
	pip install build
	python -m build --sdist --wheel --outdir dist/

lint: setup ## run python linting
	black pydantic_redis
	flake8 pydantic_redis

check-version: setup ## Check the version of the pydantic-aioredis package
	python setup.py --version

start-redis: ## Runs a copy of redis in docker 
	docker run -it -d --rm --name $(REDIS_CONTAINER_NAME) -p 6379:6379 -e REDIS_PASSWORD=password bitnami/redis || echo "$(REDIS_CONTAINER_NAME) is either running or failed"

stop-redis: ## Stops the redis in docker
	docker stop $(REDIS_CONTAINER_NAME)
