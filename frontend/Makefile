.PHONY: docker

COMMIT_HASH := $(shell git rev-parse --short HEAD)

DOCKER_IMAGE := suever/matl-online-frontend:$(COMMIT_HASH)

docker:
	docker build -f Dockerfile -t suever/matl-online-frontend .
	docker tag suever/matl-online-frontend $(DOCKER_IMAGE)
