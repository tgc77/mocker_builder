##########################################################################################
# mocker-builder
##########################################################################################
# Testing tools for mocking and patching based on pytest_mock mocker features.
# Maintained by Tiago G Cunha
# Backport available from:
# https://pypi.org/project/mocker-builder
##########################################################################################
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from importlib import import_module
import inspect
from types import ModuleType
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    NewType,
    Optional,
    Tuple,
    TypeVar,
    Union,
)
from unittest.mock import (
    MagicMock,
    DEFAULT,
    _patch as Patch,
)
from pytest_mock import MockFixture
from mock import AsyncMock
import pytest
import warnings
import asyncio

MockType = NewType('MockType', MagicMock)
_TMockType = TypeVar('_TMockType', bound=Union[MockType, AsyncMock])
TargetType = TypeVar('TargetType', Callable, ModuleType, str)
TypeNew = TypeVar('TypeNew', bound=Any)
NewCallableType = TypeVar('NewCallableType', bound=Optional[Callable])
ReturnValueType = TypeVar('ReturnValueType', bound=Optional[Any])
SideEffectType = TypeVar('SideEffectType', bound=Optional[Union[Callable, List]])
AttrType = TypeVar('AttrType', bound=Union[Callable, str])
MockMetadataKwargsType = TypeVar('MockMetadataKwargsType', bound=Dict[str, Any])
FixtureType = TypeVar('FixtureType', bound=Callable[..., object])
PatchType = TypeVar('PatchType', bound=Patch)


class MockerBuilderWarning:
    """Base class for all warnings emitted by mocker-builder."""

    @staticmethod
    def warn(message: str, *args):
        msg = f"\033[93m{message}\033[0m"
        warnings.warn(message=msg, category=UserWarning)


class MockerBuilderException(Exception):
    """ Exception in MockerBuilder usage or invocation"""

    def __init__(self, *args: object) -> None:
        import ipdb
        ipdb.set_trace()
        # TODO set text to RED
        super().__init__(*args)


@dataclass
class TMockMetadata:
    target_path: str = None
    is_async: bool = False
    patch_kwargs: Dict[str, Any] = field(default_factory=lambda: {})
    _patch: PatchType = None
    _mock: _TMockType = None
    is_active: bool = False  # TODO we need to work on when patch.stop() called

    @property
    def return_value(self) -> ReturnValueType:
        return self.patch_kwargs.get('return_value')

    @return_value.setter
    def return_value(self, value: ReturnValueType):
        self.patch_kwargs['return_value'] = value

    @property
    def side_effect(self) -> SideEffectType:
        return self.patch_kwargs.get('side_effect')

    @side_effect.setter
    def side_effect(self, value: SideEffectType):
        self.patch_kwargs['side_effect'] = value

    @property
    def configure_mock(self) -> MockMetadataKwargsType:
        return self.patch_kwargs.get('configure_mock')

    @configure_mock.setter
    def configure_mock(self, data: MockMetadataKwargsType):
        self.patch_kwargs['configure_mock'] = data

    @property
    def new(self) -> TypeNew:
        return self.patch_kwargs.get('new')


class Patcher:
    _mocker: MockFixture = None

    @staticmethod
    def _asyncio_future(result) -> asyncio.Future:
        future = asyncio.Future()
        future.set_result(result)
        return future

    @staticmethod
    def _patch(
        mock_metadata: TMockMetadata
    ) -> TMocker.TMockType:
        if mock_metadata.is_async:
            mock_metadata.return_value = Patcher._asyncio_future(mock_metadata.return_value)

        _configure_mock = {}
        if mock_metadata.configure_mock:
            _configure_mock = mock_metadata.patch_kwargs.pop('configure_mock')

        _patch = Patcher._mocker.mock_module.patch(
            mock_metadata.target_path,
            **mock_metadata.patch_kwargs
        )
        _mocked = _patch.start()
        mock_metadata.is_active = True
        if mock_metadata.new == DEFAULT and _configure_mock:
            _mocked.configure_mock(**_configure_mock)

        Patcher._mocker._patches.append(_patch)
        mock_metadata._patch = _patch
        mock_metadata._mock = _mocked
        if hasattr(_mocked, "reset_mock"):
            Patcher._mocker._mocks.append(_mocked)

        _tmock = TMocker.TMockType(
            mock_metadata
        )
        return _tmock


@dataclass
class TMockMetadataBuilder:
    _mock_metadata: TMockMetadata = None
    __mock_keys_validate: List = field(default_factory=lambda: [
        'new',
        'spec',
        'create',
        'spec_set',
        'autospec',
        'new_callable',
        'return_value',
        'side_effect',
        'configure_mock'
    ])
    __bypass_methods: List = field(default_factory=lambda: [
        '__init__'
    ])

    def __mock_kwargs_builder(
        self,
        mock_metadata_kwargs: MockMetadataKwargsType
    ) -> MockMetadataKwargsType:
        kwargs = {}
        for attr in self.__mock_keys_validate:
            valeu = mock_metadata_kwargs.get(attr)
            if valeu:
                kwargs.update({attr: valeu})
        self._mock_metadata.patch_kwargs = kwargs

    def __apply_bypass_methods_return_value(self):
        if self._mock_metadata.target_path.rsplit('.', 1)[-1] in self.__bypass_methods:
            self._mock_metadata.return_value = None

    def __unpack_params(self, mock_metadata_kwargs: MockMetadataKwargsType) -> Tuple:
        wanted_params = [
            'target', 'method', 'attribute', 'return_value', 'side_effect'
        ]
        result = []
        for param in wanted_params:
            result.append(mock_metadata_kwargs.get(param))
        return tuple(result)

    def __call__(
        self,
        **kwargs
    ) -> TMockMetadata:
        target, method, attribute, return_value, side_effect = self.__unpack_params(kwargs)
        if return_value and side_effect:
            MockerBuilderWarning.warn(
                " Detected both return_value and side_effect keyword arguments passed to "
                f"mocker {target} "
                "Be aware that side_effect cancels return_value, unless you define the return "
                "of side_effect as DEFAULT, so have fun!"
            )
        if method and attribute:
            raise MockerBuilderException(
                "Detected both method and attribute keyword arguments passed to "
                f"mock {target}. Be aware that the method keyword sets a method mock and "
                "the attribute keyword sets an attribute mock. You can not use both together. "
                "So make your choice."
            )
        try:
            attr = method if method else attribute if attribute else None
            if inspect.isclass(target):
                _target_path = tuple(filter(None, [target.__module__, target.__name__, attr]))
            elif inspect.isroutine(target):
                try:
                    klass, attr = target.__qualname__.rsplit('.', 1)
                    _target_path = (target.__module__, klass, attr)
                except ValueError:
                    _target_path = (target.__module__, target.__name__)
            elif inspect.ismodule(target):
                _target_path = (target.__name__, attr)
            elif isinstance(target, str):
                try:
                    module, module_or_klass, attr = target.rsplit('.', 1)
                    _target_path = (module, module_or_klass, attr)
                except ValueError:
                    module, attr = target.rsplit('.', 1)
                    _target_path = (module, attr)
            else:
                raise MockerBuilderException(
                    "### Mock target not identified so just aborting. "
                    "Please check your parameters. ###"
                )
            mock_target_path = ".".join(_target_path)
            import re
            safe_mock_target_path = re.sub(r'[^A-Za-z0-9_.]+', '', mock_target_path)
            if safe_mock_target_path != mock_target_path:
                raise MockerBuilderException(
                    "Target path, method or attribute have not allowed caracters"
                )
            check_mock_target = self.__load_safe_mock_target_path_from_module(_target_path)
            self._mock_metadata = TMockMetadata()
            if inspect.iscoroutinefunction(check_mock_target):
                self._mock_metadata.is_async = True
                # TODO: Implementar return_value e/ou side_effect condicional Ex if result:...
                # TODO testar usar side_effect com future...

            self._mock_metadata.target_path = mock_target_path
            self.__mock_kwargs_builder(kwargs)
            self.__apply_bypass_methods_return_value()
            return self._mock_metadata
        except Exception as ex:
            raise MockerBuilderException(ex)

    def __load_safe_mock_target_path_from_module(self, safe_target_path: Tuple[str]):
        try:
            try:
                module_path, klass_or_module, attr = safe_target_path
            except ValueError:
                module_path, attr = safe_target_path
                module = import_module(module_path)
                module_attr = getattr(module, attr)
                if module_attr:
                    return module_attr
                return module

            module = import_module(module_path)
            is_klass = getattr(module, klass_or_module)
            if inspect.isclass(is_klass):
                klass_attr = getattr(is_klass, attr)
                if klass_attr:
                    return klass_attr
                return is_klass
            is_module = getattr(module, klass_or_module)
            if inspect.ismodule(is_module):
                module_attr = getattr(is_module, attr)
                if module_attr:
                    return module_attr
                return is_module
        except Exception as ex:
            raise MockerBuilderException(ex)


class TMocker:

    @staticmethod
    def add(
        mock_metadata: TMockMetadata
    ) -> TMocker.TMockType:
        _mock = Patcher._patch(
            mock_metadata
        )
        return _mock

    @dataclass
    class _TMock(Generic[_TMockType]):
        mock_metadata: TMockMetadata = None

        def __call__(self) -> MockType:
            return self.__get_mock()

        def __get_mock(self) -> _TMockType:
            return self.mock_metadata._mock

        def set_result(self, result: ReturnValueType):
            self.mock_metadata.return_value = result
            _mock = Patcher._patch(
                self.mock_metadata
            )
            self.mock_metadata = _mock.mock_metadata

        def start(self):
            self.mock_metadata._mock = self.mock_metadata._patch.start()
            print(f"Mock {self.__get_mock()} started...")

        def stop(self):
            self.mock_metadata._patch.stop()
            print(f"Mock {self.__get_mock()} stopped...")

    TMockType = _TMock[_TMockType]


TFixtureContentType = TypeVar('TFixtureContentType')


class MockerBuilder(ABC):

    def initializer(fnc):
        @pytest.fixture(autouse=True)
        def builder(test_main_class, mocker: MockFixture):
            """Decorator which inject a fixture to the TestClass method decorated with this
            so we can get the mocker fixture injected to be used all spread on the tests.

            Args:
                test_main_class: The pytest main TestClass which runs all tests.
                mocker: pytest-mock fixture to create patch and so on.
            """
            print("\n################# Mocker Builder Initializer ################")
            Patcher._mocker = mocker
            fnc(test_main_class)
        return builder

    @abstractmethod
    def mocker_builder_setup(self):
        """You need to setup your tests initializing mocker builder features just like that:

            TestYourClassOfTests(MockerBuilder):

                @MockerBuilder.initializer
                def mocker_builder_setup(self):
                    ...
        """
        pass

    def add_mock(
        self,
        target: TargetType,
        method: AttrType = None,
        attribute: AttrType = None,
        new: TypeNew = DEFAULT,
        spec: bool = None,
        create: bool = False,
        spec_set: bool = None,
        autospec: Union[bool, Callable] = None,
        new_callable: NewCallableType = None,
        return_value: ReturnValueType = None,
        side_effect: SideEffectType = None,
        is_async: bool = False,
        configure_mock: MockMetadataKwargsType = None
    ) -> TMocker.TMockType:
        return TMocker.add(
            TMockMetadataBuilder()(
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
                is_async=is_async,
                configure_mock=configure_mock
            )
        )

    def add_fixture(
        self,
        content: TFixtureContentType,
        # scope: str = "function"
    ) -> TFixtureContentType:
        # TODO We will work on this feature soon
        # _fixture = pytest.fixture(scope=scope)(fixture_content)
        # fixture_request = FixtureRequest(_fixture).getfixturevalue()
        # def the_fixture(_fixture) -> content.__class__:
        # result = yield content
        # print("### Gonna clean up fixture_content...")
        return content


# def fixture_content(
#     _content: TFixtureContentType
# ) -> Generator[TFixtureContentType, None, None]:
#     yield cast(_content.__class__, _content)
#     print("### Gonna clean up fixture_content...")

# def pytest_configure(config: Config):
#     class Plugin:

#         @pytest.fixture(autouse=True)
#         def fix(self):
#             assert type(self) is Plugin

#     config.pluginmanager.register(Plugin())
