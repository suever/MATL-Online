COMMIT_HASH := $(shell git rev-parse --short HEAD)

docker:
	docker build -f ops/Dockerfile -t suever/matl-online .

deploy:
	docker tag suever/matl-online suever/matl-online:$(COMMIT_HASH)
	docker push suever/matl-online:$(COMMIT_HASH)
	helm template ops \
		--set CommitHash=$(COMMIT_HASH) \
		--values ops/values/default.yaml | \
		kubectl apply -f -
