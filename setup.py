from setuptools import find_packages, setup

setup(
    name='mocker-builder',
    packages=find_packages(include=['mocker_builder']),
    version='0.1.0',
    description='Python library to build mock tests dynamicaly',
    author='Tiago G Cunha',
    license='MIT',
    install_requires=[
        'asyncio',
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
