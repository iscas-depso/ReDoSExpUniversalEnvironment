default: help

# The general philosophy and functionality of this makefile is shamelessly stolen from compiler explorer

help: # with thanks to Ben Rady
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

PODMAN=podman

.PHONY: build
build:  ## build the container
	$(PODMAN) build -t fuzz-container .
	touch .built

.built: Dockerfile
	$(MAKE) build

.PHONY: run
run: .built  ## run the container
	$(PODMAN) run --user=fuzzy --cap-drop=all --network none -it fuzz-container
