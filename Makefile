.PHONY: frontend

COMMIT_HASH := $(shell git rev-parse --short HEAD)

DOCKER_IMAGE := suever/matl-online:$(COMMIT_HASH)

docker:
	docker build -f Dockerfile -t suever/matl-online .
	docker tag suever/matl-online $(DOCKER_IMAGE)

frontend/docker:
	$(MAKE) -C frontend docker

test:
	MATL_ONLINE_ENV=test \
		pytest \
		--verbose \
		--cov-report=html \
		--cov-report=term \
		--cov=matl_online \
		tests

integration-tests:
	docker compose \
		-f docker-compose.yml \
		-f docker-compose.test.yml \
		run tests

reformat:
	black .

format-check:
	black . --check

type-check:
	mypy

flake8:
	flake8 .

lint: type-check format-check flake8

frontend:
	yarn --cwd frontend start
