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
from pytest_mock.plugin import AsyncMockType
import pytest
import warnings
import asyncio

MockType = NewType('MockType', MagicMock)
_TMockType = TypeVar('_TMockType', bound=Union[MockType, AsyncMockType])
TargetType = TypeVar('TargetType', Callable, ModuleType, str)
AttrType = TypeVar('AttrType', bound=str)
TypeNew = TypeVar('TypeNew', bound=Any)
NewCallableType = TypeVar('NewCallableType', bound=Optional[Callable])
ReturnValueType = TypeVar('ReturnValueType', bound=Optional[Any])
SideEffectType = TypeVar('SideEffectType', bound=Optional[Union[Callable, List]])
MockMetadataKwargsType = TypeVar('MockMetadataKwargsType', bound=Dict[str, Any])
FixtureType = TypeVar('FixtureType', bound=Callable[..., object])
PatchType = TypeVar('PatchType', bound=Patch)

__version__ = "0.1.0"


class MockerBuilderWarning:
    """Base class for all warnings emitted by mocker-builder"""

    @staticmethod
    def warn(message: str, *args):
        msg = f"\033[93m{message}\033[0m"
        warnings.warn(message=msg, category=UserWarning)


class MockerBuilderException(Exception):
    """Exception in MockerBuilder usage or invocation"""


@dataclass
class TMockMetadata:
    """Mock metadata structure to keep state of created mock and patcher for easily reset mock
    return value and so on.

    Args:
        target_path (str): Keep converted mock patch target and attribute users enter as class 
        method or attribute or even module methods or attributes so we can just patch them.

        is_async: (bool): Identify if method to be mocked is async or not.

        patch_kwargs: (MockMetadataKwargsType): Here we just dispatch kwargs mock parameters such as
        return_value, side_effect, spec, new_callable, configure_mock and so on.

        _patch: (PatchType): Mocker patch wrapper to create and start mocks.

        _mock: (_TMockType): Mock instance keeper.

        is_active: (bool): Flag to sinalize that mock is active.
        (We really don't know how gonna use that yet, hehe!)
    """
    target_path: str = None
    is_async: bool = False
    patch_kwargs: MockMetadataKwargsType = field(default_factory=lambda: {})
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
    """Patch wrapper for the mocker.patch feature.

    Args:
        _mocker (MockFixture): mocker fixture keeper.
    """
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
        """Our mock patch to properly identify and setting mock properties. We start the mock so
        we can manage state when stopping and restarting mocks.

        Args:
            mock_metadata (TMockMetadata): Mock metadata instance with mock's data.

        Returns:
            TMocker.TMockType: Our Mock Type wrapper.
        """
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
    """Here we build our mock metada to parse mock parameters and propagate state.

    Args:
        _mock_metadata (TMockMetadata): Mock metadata instance to propagate mock state.

        __mock_keys_validate (List[str]): Mock parameters we need to check if were setted to 
        dispatch to mock.patch creation.

        __bypass_methods (List[str]): Methods we need keeping properly behavior for return value.

    Raises:
        MockerBuilderException: Notify users when we found in trouble.

    """
    _mock_metadata: TMockMetadata = None
    __mock_keys_validate: List[str] = field(default_factory=lambda: [
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
    __bypass_methods: List[str] = field(default_factory=lambda: [
        '__init__'
    ])

    def __mock_kwargs_builder(
        self,
        mock_metadata_kwargs: MockMetadataKwargsType
    ):
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
        """Mock metadata builder by parsing mock parameters and setting our mock_metadata instance.

        Raises:
            MockerBuilderException: Notify users when we found in trouble.

        Returns:
            TMockMetadata: Mock metadata to keep mock and patch state and creation.
        """
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
            # Here we need to parse the target parameter to identify the type and spliting by
            # package/module, module, class and method or attribute we are going to mock converting
            # the path to string.
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
        # Here we just validate if our parsed target args are importable to be able to check in
        # the future if a method is async or not.
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
    """Our interface to handle mock features"""

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
        """Our specialized Mock to handle with MagicMock or AsyncMock types.

        Args:
            Generic (_TMockType): Mock type we give back to user's tests.

            mock_metadata (TMockMetadata): Mock metadata instance given from MockMetadata Builder.
        """
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
    """Our interface to connect mock metadata builder to the user's building tests"""

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
        """From here we create new mock.patch parsing the :param target parameter. You can just set your
        target as normal imported class, module or method. You don't need to pass it as string like
        normal mock.patch does. Here we make it easier by just allowing to set the :param target parameter
        for classes, modules and methods or functions without the need of setting the :param method 
        parameter. Just if you wanna mock an attribute you must set it from the :param attribute
        parameter as string. The target can be am imported class or module but the attribute need 
        to be passed as string:

            from testing_heroes.my_heroes import MyHeroes

            class TestMyHeroes(MockerBuilder):

                @MockerBuilder.initializer
                def mocker_builder_setup(self):

                    self.mock_my_hero_attribute = self.add_mock(
                        target=MyHeroes,
                        attribute='_my_hero',
                        configure_mock={
                            'eating_banana.return_value': "Banana Noooo!",
                            'just_says.side_effect': ["Nothing to say!"]
                        }
                    )

                def test_my_hero_attribute(self):
                    assert self.mock_my_hero_attribue().eating_banana() == "Banana Noooo!"
                    assert self.mock_my_hero_attribue().just_says() == "Nothing to say!"

        Types description:
            TargetType = TypeVar('TargetType', Callable, ModuleType, str)
            AttrType = TypeVar('AttrType', bound=Union[Callable, str])
            TypeNew = TypeVar('TypeNew', bound=Any)
            NewCallableType = TypeVar('NewCallableType', bound=Optional[Callable])
            ReturnValueType = TypeVar('ReturnValueType', bound=Optional[Any])
            SideEffectType = TypeVar('SideEffectType', bound=Optional[Union[Callable, List]])

        Args:
            target (TargetType): The target to be mocked.

            method (AttrType[str], optional): Method to be mocked, useful when need to create
                an method or dynamically invoking. Defaults to None.

            attribute (AttrType[str], optional): Attribute to be mocked. Defaults to None.

            new (TypeNew, optional): The new type that target.attibute
                will get after mocking. Defaults to DEFAULT.
                Ex: ... self.add_mock(
                    target=MyClass,
                    attribute='my_class_attr',
                    new=PropertyMock(OtherClass) # A Mock with spec of OtherClass.
                        or
                    new=OtherClass # A real class, not a mock.
                )

            spec (bool, optional): _description_. Defaults to None.

            create (bool, optional): _description_. Defaults to False.

            spec_set (bool, optional): _description_. Defaults to None.

            autospec (Union[bool, Callable], optional): _description_. Defaults to None.

            new_callable (NewCallableType, optional): _description_. Defaults to None.

            return_value (ReturnValueType, optional): _description_. Defaults to None.

            side_effect (SideEffectType, optional): _description_. Defaults to None.

            is_async (bool, optional): _description_. Defaults to False.

            configure_mock (MockMetadataKwargsType, optional): _description_. Defaults to None.

        Returns:
            TMocker.TMockType: _description_
        """
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
