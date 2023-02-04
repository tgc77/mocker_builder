
build:
	echo "Building dist..."
	# python setup.py sdist bdist_wheel
	echo "Done"

	echo "Checking dist..."
	# twine check dist/*
	echo "Done"

test-upload: build
	python -m twine upload --repository testpypi dist/*

test-install:
	python3 -m pip install --index-url https://test.pypi.org/mocker-builder/ --no-deps mocker-builder-tiago77.py

upload:
	twine upload dist/*

.PHONY: build test-upload upload test-install
