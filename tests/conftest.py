import pytest
from collections import namedtuple

TestCase = namedtuple("TestCase", ["text", "expected"])


@pytest.fixture(
    params=[
        TestCase("hello", "english"),
        TestCase("hola", "spanish"),
        TestCase("bonjour", "french")
    ]
)
def test_case(request):
    return request.param
