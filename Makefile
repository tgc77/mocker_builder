
DOCS_DIR := $(shell pwd)/docs

build: clean
	python setup.py sdist bdist_wheel
	twine check dist/*

test-upload: build
	python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*

test-install:
	python3 -m pip install --index-url https://test.pypi.org/mocker-builder/ --no-deps mocker-builder-tiago77.py

upload: build
	twine upload dist/*

clean:
	$(info Cleaning previos build files)
	rm -rf ./build ./dist

run-demo:
	python -m pytest test_cases/main.py -vv -s -x

html-doc:
	cd $(DOCS_DIR); \
	make html

clean-html-doc:
	cd $(DOCS_DIR); \
	make clean

.PHONY: build test-upload upload test-install clean run-demo html-doc clean-html-doc
