
build:
	$(info Building dist...)
	python setup.py sdist bdist_wheel
	$(info Done)

	$(info Checking dist...)
	twine check dist/*
	$(info Done)

test-upload: build
	python -m twine upload --repository testpypi dist/*

test-install:
	python3 -m pip install --index-url https://test.pypi.org/mocker-builder/ --no-deps mocker-builder-tiago77.py

upload:
	twine upload dist/*

clean:
	$(info Cleaning previos build files)
	rm -rf ./build ./dist

.PHONY: build test-upload upload test-install clean
