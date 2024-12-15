.DEFAULT_GOAL := help

run:
	python3 RaumfeldControl.py
build:
	docker build -t pyraumfeld .

run-docker:
	docker run --rm -it --network host pyraumfeld

help:
	@echo "Available targets:"
	@echo "  run          - Run the RaumfeldControl API"
	@echo "  build        - Build the Docker image"
	@echo "  run-docker   - Run the Docker container"