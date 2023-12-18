VERSION=$(shell git describe --tags --dirty --always)

.PHONY: build
build:
	sed -i '/^app-version:/c\app-version: ${VERSION}' auterion-app.yml
	auterion-cli app build

install:
	auterion-cli app install