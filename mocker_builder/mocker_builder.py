# from __future__ import annotations
# mocker_builder.py
# Test tools for mocking and patching.
# Maintained by Tiago G Cunha
# Backport for other versions of Python available from
# https://pypi.org/project/mocker-builder


from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass, field
from importlib import import_module
from types import ModuleType
from typing import (
    Any, Callable, Dict, Generic, List, NewType, Optional, Tuple, TypeVar, Union
)
import inspect
import warnings
from unittest.mock import DEFAULT, MagicMock, _patch
import pytest
from pytest_mock import MockerFixture
from pytest_mock.plugin import AsyncMockType

_MockType = TypeVar('_MockType', bound=Union[MagicMock, AsyncMockType])
_TP = TypeVar('_TP', bound=_patch)  # or can be _MockType


MockType = NewType('MockType', MagicMock)
_TMockType = TypeVar('_TMockType', bound=MockType)
TargetType = TypeVar('TargetType', Callable, ModuleType, str)
TypeNew = TypeVar('TypeNew', bound=Any)
NewCallableType = TypeVar('NewCallableType', bound=Optional[Callable])
ReturnValueType = TypeVar('ReturnValueType', bound=Optional[Any])
SideEffectType = TypeVar('SideEffectType', bound=Optional[Union[Callable, List]])
AttrType = TypeVar('AttrType', bound=Union[Callable, str])


__version__ = "1.0"


class MockerBuilderWarning(UserWarning):
    """Base class for all warnings emitted by mocker-builder."""


class MockerBuilderException(Exception):
    """ Exception in MockerBuilder usage or invocation"""

    def __repr__(self) -> str:
        return "This is MockerBuilderException, ouieh!"


class Patcher(Generic[_TP]):
    pass


@dataclass
class MockMetadata:
    mock_name: str
    target: TargetType = None
    method: AttrType = None
    attribute: AttrType = None
    new: TypeNew = DEFAULT
    spec: bool = None
    create: bool = False
    spec_set: bool = None
    autospec: Union[bool, Callable] = None
    new_callable: NewCallableType = None
    return_value: ReturnValueType = None
    side_effect: SideEffectType = None
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
        self._mocked_method: Dict[str, _MockType] = {}
        self._mock_metadata: Dict[str, MockMetadata] = {}
        self._current_mock: MockMetadata = None
        self._test_main_class = None
        self.load_args: list = None

    def _register_test_main_class(self, t_main_class: Callable):
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

    def __patcher(self, mock_metadata: MockMetadata) -> Patcher[_TP]:
        """_summary_

        Args:
            mock_metadata (MockMetadata): _description_

        Returns:
            Union[MagicMock, AsyncMockType]: _description_
        """
        _, target, method, attribute, *_ = mock_metadata.unpack()
        _args = list(filter(None, [method if method else attribute]))
        _kwargs = self._mock_kwargs_builder(mock_metadata)
        _patch_args = [target, *_args]
        # import ipdb
        # ipdb.set_trace()
        # TODO IS GONNA GET EASIER IF WE JUST VALIDATE AND PATCH AS STRING
        # PERHAPS WE'LL NEED TO TEST IF PATCH WORKS WITH MODULE/CLASS ATTRIBUTES MOCKING
        if inspect.isclass(target):
            if not _args:
                return self._mocker.patch(
                    ".".join(self.load_args),
                    **_kwargs
                )
            return self._mocker.patch.object(
                *_patch_args,
                **_kwargs
            )
        # TODO should we check if target is a valid module? It may be a package!
        if inspect.ismodule(target):
            if not _args:
                return self._mocker.patch(
                    *self.load_args,
                    **_kwargs
                )
            return self._mocker.patch.object(
                *_patch_args,
                **_kwargs
            )
        if inspect.isroutine(target):
            target = ".".join([target.__module__, target.__qualname__])
            return self._mocker.patch(
                target,
                **_kwargs
            )
        # TODO Test with dicts
        if isinstance(target, dict):
            return self._mocker.patch.dict(
                *_patch_args,
                **_kwargs
            )
        if isinstance(target, str):
            return self._mocker.patch(
                *_patch_args,
                **_kwargs
            )
        # TODO We must test using patch.multiple(...)
        if isinstance(target, list):
            return self._mocker.patch.multiple(
                *[*_patch_args.pop(0), *_patch_args],
                **_kwargs
            )

    def __load_safe_mock_param_path_from_module(self, path_attr: str):
        """_summary_

        Args:
            path_attr (str): _description_

        Returns:
            _type_: _description_
        """
        # TODO: You should save state of the imported mock target so we can use it along
        # the process flow
        # import ipdb
        # ipdb.set_trace()
        path, attr = path_attr.rsplit('.', 1)
        # if attr is '' so we know that our mock don't have attribute nor method kwargs setted.
        # So we need to look if the mock came from a class or a module.
        if not attr:
            # Flow without attribute nor method setted.
            # Here we know that klass may not be a class really and so we need to check if it's
            # a method or an attribute that can come from a class or a module.
            module, attr = path.rsplit('.', 1)
            try:
                if isinstance(import_module(module), ModuleType):
                    # Here we know that module is really a module, ouieh!
                    # TODO perhaps we will use that way
                    # self._current_mock.target = getattr(import_module(module), attr)
                    return getattr(import_module(module), attr)
            except ModuleNotFoundError:
                # Here we check if module actually is a class
                try:
                    module, klass = module.rsplit('.', 1)
                    is_class = getattr(import_module(module), klass)
                    if inspect.isclass(is_class):
                        return getattr(is_class, attr)
                except ModuleNotFoundError:
                    # Here we don't know really what's coming!
                    print("### Not identified from where method or attribute is coming from!")
                    try:
                        what_is_that = getattr(import_module(path), attr)
                        what_is_this = getattr(import_module(module), klass)
                        return what_is_that if attr else what_is_this
                    except Exception as e:
                        raise MockerBuilderException(e)
        else:
            # Flow with attribute or method setted
            try:
                if isinstance(import_module(path), ModuleType):
                    # Here we now that module is really a module, ouieh!
                    return getattr(import_module(path), attr)
            except ModuleNotFoundError:
                module, klass = path.rsplit('.', 1)
                is_class = getattr(import_module(module), klass)
                if inspect.isclass(is_class):
                    return getattr(is_class, attr)

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
            warnings.warn(
                "\033[93mDetected both return_value and side_effect keyword arguments passed to "
                f"mocker {mock_name}. "
                "Be aware that side_effect cancels return_value, unless you define the return "
                "of side_effect as DEFAULT, so have fun!\033[0m"
            )

        if method and attribute:
            attribute = None
            warnings.warn(
                "\033[93mDetected both method and attr keyword arguments passed to "
                f"mocker {mock_name}. Be aware that the method keyword sets a method mock and "
                "the attr keyword sets an attribute mock. Method mock has priority and will be used"
                ", so use it wiselly and have fun!\033[0m"
            )
        try:
            if inspect.isclass(target):
                self.load_args = [target.__module__, target.__name__]
            elif inspect.isroutine(target):
                self.load_args = [target.__module__, target.__qualname__]
            elif inspect.ismodule(target):
                self.load_args = [target.__name__]
            elif isinstance(target, str):
                self.load_args = [target]
            else:
                warnings.warn(
                    "###\033[93m target not identified so just dispatching as we received.\033[0m"
                )
                self.load_args = [target]

            mock_param_path = ".".join(
                [*self.load_args, method if method else attribute if attribute else '']
            )
            import re
            safe_mock_param_path = re.sub(r'[^A-Za-z0-9_.]+', '', mock_param_path)
            check_mock_param = self.__load_safe_mock_param_path_from_module(safe_mock_param_path)

            if inspect.iscoroutinefunction(check_mock_param):
                future = asyncio.Future()
                future.set_result(return_value)
                self._current_mock.return_value = future
                # TODO: Implementar return_value e/ou side_effect condicional Ex if result:...
                # TODO testar usar side_effect com future...

            self._mocked_method[mock_name] = self.__patcher(self._current_mock)
            if self._current_mock.new == DEFAULT and self._current_mock.kwargs:
                self._mocked_method[mock_name].configure_mock(**self._current_mock.kwargs)
            # TODO We need to create a proper data structure to enable test_main_class
            # to have autocomplete MagicMock params
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

    def _get_mock_metadata(self, mock_name: str) -> Union[MockMetadata, None]:
        return self._mock_metadata.get(mock_name)

    def _stop_mock(self, _mock: _MockType):
        for mock in self._mocker._patches:
            if mock.get_original()[0] == _mock:
                mock.stop()
                print(f"Mock {_mock._extract_mock_name()} stopped...")
                break

    def _start_mock(self, _mock: _MockType):
        # TODO is not working, need to refactor
        for mock in self._mocker._patches:
            # if hasattr(mock.get_original()[0], '__name__'):
            if mock.get_original()[0] == _mock:
                print(f"Mock {_mock} started...")
                mock.start()
                break


class IMockerBuilder(ABC):
    """_summary_

    Args:
        ABC (_type_): _description_

    Returns:
        _type_: _description_

    Yields:
        _type_: _description_
    """
    __mocker_builder: MockerBuilderImpl = None
    __fixtures: Dict = {}
    _mocker: MockerFixture = None  # TODO We need that?

    def initializer(fnc):
        @pytest.fixture(autouse=True)
        def builder(test_main_class: IMockerBuilder, mocker):
            """_summary_

            Args:
                test_main_class (IMockerBuilder): _description_
                mocker (_type_): _description_

            Yields:
                _type_: _description_
            """
            print("\n#################### mocker_builder_create ##################")
            test_main_class.__mocker_builder = MockerBuilderImpl(mocker)
            test_main_class.__mocker_builder._register_test_main_class(test_main_class)
            # TODO Perhaps it's good to enable the mocker to the TestMainClass
            test_main_class._mocker = mocker
            fnc(test_main_class)
            yield test_main_class.mocker_builder_start()
            del test_main_class.__mocker_builder
            # TODO need to run gc.collect() or clean memory from here ?
        return builder

    @abstractmethod
    def mocker_builder_initializer(self):
        pass

    # TODO refactor the way we create and provide them
    # perhaps also for impl into this function alls fixtures and inject them instead always
    # call self.fixture_register(...)
    # TODO make return a Fixture Type so we can use like: self.my_fixture = self.fixture_register
    # perhaps change to add_fixture
    def fixture_register(
        self,
        name,
        return_value: ReturnValueType = None
    ):
        self.__fixtures.update({
            name: return_value
        })
        setattr(self, name, return_value)

    def add_mock(
        self,
        mock_name: str,
        target: TargetType,
        method: AttrType = None,
        attribute: AttrType = None,
        new: TypeNew = DEFAULT,
        spec: Optional[bool] = None,
        create: Optional[bool] = False,
        spec_set: Optional[bool] = None,
        autospec: Optional[Union[bool, Callable]] = None,
        new_callable: NewCallableType = None,
        return_value: ReturnValueType = None,
        side_effect: SideEffectType = None,
        active: Optional[bool] = True,
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
    def get_mock_metadata(self, mock_name: str) -> Union[MockMetadata, None]:
        return self.__mocker_builder._get_mock_metadata(mock_name)

    def stop_mock(self, _mock: _MockType):
        self.__mocker_builder._stop_mock(_mock)

    def start_mock(self, _mock: _MockType):
        self.__mocker_builder._start_mock(_mock)
