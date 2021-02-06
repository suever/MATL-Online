COMMIT_HASH := $(shell git rev-parse --short HEAD)

DOCKER_IMAGE := suever/matl-online:$(COMMIT_HASH)

docker:
	docker build -f ops/Dockerfile -t suever/matl-online .
	docker tag suever/matl-online $(DOCKER_IMAGE)

deploy: docker
	docker push $(DOCKER_IMAGE)
	helm template ops \
		--set CommitHash=$(COMMIT_HASH) \
		--values ops/values/default.yaml | \
		kubectl apply -f -