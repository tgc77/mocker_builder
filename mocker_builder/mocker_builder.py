# mocker_builder.py
# Test tools for mocking and patching.
# Maintained by Tiago G Cunha
# Backport for other versions of Python available from
# https://pypi.org/project/mocker-builder


from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass, field
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union
import inspect
from unittest.mock import DEFAULT, MagicMock
import pytest
from pytest_mock import MockerFixture
from pytest_mock.plugin import AsyncMockType

Tk = TypeVar('Tk', bound=Optional[Callable])
Tm = TypeVar('Tm', bound=Optional[ModuleType])
Tt = TypeVar('Tt', Callable, ModuleType, str)
Tv = TypeVar('Tv')
Tr = TypeVar('Tr', bound=Optional[Any])
Tse = TypeVar('Tse', bound=Optional[Union[Callable, List]])

__version__ = "0.1.0"


class MockerBuilderException(Exception):
    """ Exception in MockerBuilder usage or invocation"""


@dataclass
class MockMetadata:
    mock_name: str
    target: Tt = None
    method: str = None
    attribute: str = None
    new: Tv = DEFAULT
    spec: bool = None
    create: bool = False
    spec_set: bool = None
    autospec: Union[bool, Callable] = None
    new_callable: Callable = None
    return_value: Tr = None
    side_effect: Tse = None
    active: bool = True
    kwargs: Dict[str, Any] = field(default_factory={})

    def unpack(self) -> Tuple:
        return (
            self.mock_name,
            self.target,
            self.method,
            self.attribute,
            self.return_value,
            self.side_effect
        )

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False


class MockerBuilderImpl:
    """_summary_

    Returns:
        _type_: _description_
    """
    __mock_keys_validate = [
        'new',
        'spec',
        'create',
        'spec_set',
        'autospec',
        'new_callable',
        'return_value',
        'side_effect'
    ]

    def __init__(self, mocker: MockerFixture) -> None:
        self._mocker = mocker
        self._mocked_method: Dict[str, Union[MagicMock, AsyncMockType]] = {}
        self._mock_metadata: Dict[str, MockMetadata] = {}
        self._current_mock: MockMetadata = None
        self._test_main_class = None

    def _register_test_main_class(self, t_main_class: Tk):
        """_summary_

        Args:
            t_main_class (Tk): _description_
        """
        self._test_main_class = t_main_class

    def _start(self):
        self.__load_metadata()

    def _mock_kwargs_builder(self, mock_metadata: MockMetadata) -> Dict[str, Any]:
        """_summary_

        Args:
            mock_metadata (MockMetadata): _description_

        Returns:
            Dict[str, Any]: _description_
        """
        kwargs = {}
        for attr in self.__mock_keys_validate:
            valeu = getattr(mock_metadata, attr)
            if valeu:
                kwargs.update({attr: valeu})
        return kwargs

    def patcher(self, mock_metadata: MockMetadata) -> Union[MagicMock, AsyncMockType]:
        """_summary_

        Args:
            mock_metadata (MockMetadata): _description_

        Returns:
            Union[MagicMock, AsyncMockType]: _description_
        """
        target = mock_metadata.target
        method = mock_metadata.method
        attribute = mock_metadata.attribute
        _args = [method if method else attribute]
        _kwargs = self._mock_kwargs_builder(mock_metadata)

        if not isinstance(target, str):
            return self._mocker.patch.object(
                target,
                *_args,
                **_kwargs
            )
        elif isinstance(target, dict):
            return self._mocker.patch.dict(
                target,
                *_args,
                **_kwargs
            )
        else:
            return self._mocker.patch(
                target,
                *_args,
                **_kwargs
            )

    def __load_safe_mock_param_path_from_module(self, path_attr: str):
        """_summary_

        Args:
            path_attr (str): _description_

        Returns:
            _type_: _description_
        """
        from importlib import import_module
        path, attr = path_attr.rsplit('.', 1)
        module, klass = path.rsplit('.', 1)
        is_class = getattr(import_module(module), klass)

        if inspect.isclass(is_class):
            return getattr(is_class, attr)

        return getattr(import_module(path), attr)

    def __patch(
        self,
        mock_metadata: MockMetadata
    ):
        """_summary_

        Args:
            mock_metadata (MockMetadata): _description_

        Raises:
            MockerBuilderException: _description_

        Returns:
            _type_: _description_
        """
        self._current_mock = mock_metadata
        mock_name, target, method, attribute, return_value, side_effect = mock_metadata.unpack()

        if return_value and side_effect:
            import warnings
            warnings.warn(
                "\033[93mDetected both return_value and side_effect keyword arguments passed to "
                f"mocker {mock_name}. "
                "Be aware that side_effect cancels return_value, unless you define the return "
                "of side_effect as DEFAULT, so have fun!\033[0m"
            )

        if method and attribute:
            attribute = None
            import warnings
            warnings.warn(
                "\033[93mDetected both method and attr keyword arguments passed to "
                f"mocker {mock_name}. Be aware that the method keyword sets a method mock and "
                "the attr keyword sets an attribute mock. Method mock has priority and will be used"
                ", so use it wiselly and have fun!\033[0m"
            )
        try:
            if inspect.isclass(target):
                load_args = [target.__module__, target.__name__]
            elif inspect.ismodule(target):
                load_args = [target.__name__]
            elif isinstance(target, str):
                load_args = [target]

            mock_param_path = ".".join(
                [*load_args, method if method else attribute]
            )
            import re
            safe_mock_param_path = re.sub(r'[^A-Za-z0-9_.]+', '', mock_param_path)
            check_mock_param = self.__load_safe_mock_param_path_from_module(safe_mock_param_path)

            if inspect.iscoroutinefunction(check_mock_param):
                future = asyncio.Future()
                future.set_result(return_value)
                mock_metadata.return_value = future
                # TODO: Implementar return_value e/ou side_effect condicional Ex if result:...
                # TODO testar usar side_effect com future...

            self._mocked_method[mock_name] = self.patcher(mock_metadata)
            if mock_metadata.new == DEFAULT and mock_metadata.kwargs:
                self._mocked_method[mock_name].configure_mock(**mock_metadata.kwargs)
            setattr(self._test_main_class, mock_name, self._mocked_method[mock_name])
        except Exception as ex:
            raise MockerBuilderException(ex)

    def _add_mock(self, mock_metadata: MockMetadata):
        """_summary_

        Args:
            mock_metadata (MockMetadata): _description_
        """
        self._mock_metadata.update({
            mock_metadata.mock_name: mock_metadata
        })

    def __load_metadata(self):
        """_summary_
        """
        for _, mock_metadata in self._mock_metadata.items():
            if not mock_metadata.active:
                continue

            self.__patch(
                mock_metadata
            )

    def get_mock(self, mock_name: str) -> Union[MockMetadata, None]:
        return self._mock_metadata.get(mock_name)

    ###########################################################################################
    # TODO refactor to enable access mock methods asserts from our mocker-builder
    # def configure_mock(self, **kwargs):
    #     pass

    # def assert_not_called(self, *args: Any, **kwargs: Any) -> None:
    #     return self._mocker.assert_not_called

    # def assert_called_with(self, *args: Any, **kwargs: Any) -> None:
    #     return self._mocker.assert_called_with

    # def assert_called_once(self, *args: Any, **kwargs: Any) -> None:
    #     return self._mocker.assert_called_once

    # def assert_called_once_with(self, *args: Any, **kwargs: Any) -> None:
    #     return self._mocker.assert_called_once_with

    # def assert_has_calls(self, *args: Any, **kwargs: Any) -> None:
    #     return self._mocker.assert_has_calls

    # def assert_any_call(self, *args: Any, **kwargs: Any) -> None:
    #     return self._mocker.assert_any_call

    # def assert_called(self, *args: Any, **kwargs: Any) -> None:
    #     return self._mocker.assert_called

    # def assert_not_awaited(self, *args: Any, **kwargs: Any) -> None:
    #     return self._mocker.assert_not_awaited

    # def assert_awaited_with(self, *args: Any, **kwargs: Any) -> None:
    #     return self._mocker.assert_awaited_with

    # def assert_awaited_once(self, *args: Any, **kwargs: Any) -> None:
    #     return self._mocker.assert_awaited_once

    # def assert_awaited_once_with(self, *args: Any, **kwargs: Any) -> None:
    #     return self._mocker.assert_awaited_once_with

    # def assert_has_awaits(self, *args: Any, **kwargs: Any) -> None:
    #     return self._mocker.assert_has_awaits

    # def assert_any_await(self, *args: Any, **kwargs: Any) -> None:
    #     return self._mocker.assert_any_await

    # def assert_awaited(self, *args: Any, **kwargs: Any) -> None:
    #     return self._mocker.assert_awaited


class IMockerBuilder(ABC):
    __mocker_builder: MockerBuilderImpl = None
    __fixtures: Dict = {}

    def initializer(fnc):
        @pytest.fixture(autouse=True)
        def builder(test_main_class, mocker):
            print("\n#################### mocker_builder_create ##################")
            IMockerBuilder.__mocker_builder = MockerBuilderImpl(mocker)
            IMockerBuilder.__mocker_builder._register_test_main_class(test_main_class)
            setattr(test_main_class, 'mocker', mocker)
            yield fnc(test_main_class)
            # TODO need to run gc.collect() or clean memory from here ?
        return builder

    @abstractmethod
    def mocker_builder_initializer(self):
        pass

    # TODO refactor the way we create and provide them
    # perhaps also for impl into this function alls fixtures and inject them instead always
    # call self.fixture_register(...)
    def fixture_register(self, name, return_value):
        self.__fixtures.update({
            name: return_value
        })
        setattr(self, name, return_value)

    def add_mock(
        self,
        mock_name: str,
        target: Tk,
        method: str = None,
        attribute: str = None,
        new: Tv = DEFAULT,
        spec: bool = None,
        create: bool = False,
        spec_set: bool = None,
        autospec: Union[bool, Callable] = None,
        new_callable: Callable = None,
        return_value: Tr = None,
        side_effect: Tse = None,
        active: bool = True,
        **kwargs
    ):
        mock_metadata = MockMetadata(
            mock_name=mock_name,
            target=target,
            method=method,
            attribute=attribute,
            new=new,
            spec=spec,
            create=create,
            spec_set=spec_set,
            autospec=autospec,
            new_callable=new_callable,
            return_value=return_value,
            side_effect=side_effect,
            active=active,
            kwargs=kwargs if kwargs else None
        )
        self.__mocker_builder._add_mock(
            mock_metadata=mock_metadata
        )

    # TODO perhaps should we start ourselves mocker_builder instaed waiting call every test ?
    def mocker_builder_start(self):
        self.__mocker_builder._start()

    # TODO should we enable mock_metadata changes after initializer and start ?
    def get_mock(self, mock_name: str) -> Union[MockMetadata, None]:
        return self.__mocker_builder.get_mock(mock_name)
