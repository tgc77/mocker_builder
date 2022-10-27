from setuptools import setup, find_packages
from codecs import open
from os import path
from mocker_builder.mocker_builder import __version__

DESCRIPTION = path.abspath(path.dirname(__file__))

with open(path.join(DESCRIPTION, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="mocker-builder",
    version=__version__,
    description="Python library to build mock tests dynamicaly using the mocker "
    "feature from pytest-mock lib",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://mocker-builder.readthedocs.io/",
    author="Tiago G Cunha",
    author_email="tikx.batera@gmail.com",
    license="MIT",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent"
    ],
    packages=find_packages(include=['mocker_builder']),
    include_package_data=True,
    install_requires=[
        'pytest',
        'pytest_mock'
    ],
    setup_requires=['pytest-runner'],
    tests_require=[
        'pytest',
        'pytest_mock'
    ],
    test_suite='tests',
)
