import asyncio
from importlib import import_module
import inspect
import pytest
from pytest_mock import MockFixture
from types import ModuleType
from typing import (
    Any,
    Callable,
    List,
    Optional,
    Union,
)
from unittest.mock import (
    MagicMock,
    DEFAULT
)


class _Mocker:
    _instace: MockFixture

    def patch(
        self,
        target: Union[Callable, ModuleType, str],
        attribute: str = None,
        new: Any = DEFAULT,
        spec: bool = None,
        create: bool = False,
        spec_set: bool = None,
        autospec: Union[bool, Callable] = None,
        new_callable: Optional[Callable] = None,
        return_value: Optional[Any] = None,
        side_effect: Optional[Union[Callable, List]] = None,
        **kwargs
    ) -> MagicMock:
        if isinstance(target, str):
            path, attribute = target.rsplit('.', 1)
            target = import_module(path)
        target_attr = getattr(target, attribute)
        if inspect.iscoroutinefunction(target_attr):
            future = asyncio.Future()
            future.set_result(return_value)
            return_value = future
        return _Mocker._instace.patch.object(
            target=target,
            attribute=attribute,
            new=new,
            spec=spec,
            create=create,
            spec_set=spec_set,
            autospec=autospec,
            new_callable=new_callable,
            return_value=return_value,
            side_effect=side_effect,
            **kwargs
        )

    def inject(fnc):
        @pytest.fixture(autouse=True)
        def builder(test_main_class, mocker: MockFixture):
            """Decorator which inject a fixture to the TestClass method decorated with this
            so we can get the mocker fixture injected to be used all spread on the tests.

            Args:
                test_main_class: The pytest main TestClass which runs all tests.
                mocker: pytest-mock fixture to create patch and so on.
            """
            _Mocker._instace = mocker
            yield fnc(test_main_class)
        return builder
