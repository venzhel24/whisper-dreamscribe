.PHONY: build push deploy clean

IMAGE_NAME = venzhel24/whisper-dreamscribe
TAG = latest

build:
	docker build -t $(IMAGE_NAME):$(TAG) .

push: build
	docker push $(IMAGE_NAME):$(TAG)

deploy:
	docker-compose pull
	docker-compose up -d

clean:
	docker image prune -f
	docker container prune -f

dev:
	docker-compose -f docker-compose.dev.yml up --build

logs:
	docker-compose logs -f whisper-dreamscribe
