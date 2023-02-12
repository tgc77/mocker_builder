
build:
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

.PHONY: build test-upload upload test-install clean