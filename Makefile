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
	kubectl rollout status -n matl-online deploy/web
	kubectl rollout status -n matl-online deploy/worker


test:
	MATL_ONLINE_ENV=test \
		pytest \
		--verbose \
		--cov-report=html \
		--cov-report=term \
		--cov=matl_online \
		tests

integration-tests:
	docker-compose \
		-f docker-compose.yml \
		-f docker-compose.test.yml \
		run tests

reformat:
	black .

format-check:
	black . --check

flake8:
	flake8 .

