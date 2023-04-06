###################################################################################################
# mocker-builder
###################################################################################################
# Testing tools for mocking and patching based on pytest_mock mocker features, but with improvements.
# Maintained by Tiago G Cunha
# Backport available from:
# https://pypi.org/project/mocker-builder
###################################################################################################
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
    Type,
    TypeVar,
    Union,
)
from unittest.mock import (
    MagicMock,
    DEFAULT,
    _patch as _PatchType,
)
from mock import AsyncMock
from pytest_mock import MockFixture
import pytest
import warnings

MockType = NewType('MockType', MagicMock)
AsyncMockType = NewType('AsyncMockType', AsyncMock)
_TMockType = TypeVar('_TMockType', bound=Union[MockType, AsyncMockType])
TargetType = TypeVar('TargetType', Callable, ModuleType, str)
AttrType = TypeVar('AttrType', bound=str)
TypeNew = TypeVar('TypeNew', bound=Any)
NewCallableType = TypeVar('NewCallableType', bound=Optional[Callable])
ReturnValueType = TypeVar('ReturnValueType', bound=Optional[Any])
SideEffectType = TypeVar('SideEffectType', bound=Optional[Union[Callable, List]])
MockMetadataKwargsType = TypeVar('MockMetadataKwargsType', bound=Dict[str, Any])
FixtureType = TypeVar('FixtureType', bound=Callable[..., object])
_Patch = TypeVar('_Patch', bound=_PatchType)

__version__ = "0.1.4"


class MockerBuilderWarning:
    """Base class for all warnings emitted by mocker-builder"""

    @staticmethod
    def warn(message: str):
        msg = f"\033[93m{message}\033[0m"
        warnings.warn(message=msg, category=UserWarning)


class MockerBuilderException(Exception):
    """Raised Exception in MockerBuilder usage or invocation"""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


@dataclass
class TMockMetadata:
    """Mock metadata structure to keep state of created mock and patcher for easily reset mock
    return value and so on.

    Args:
        target_path (str):
            Keep converted mock patch target and attribute users enter as class
            method or attribute or even module methods or attributes so we can just patch them.

        is_async: (bool):
            Identify if method to be mocked is async or not.

        patch_kwargs: (MockMetadataKwargsType):
            Here we just dispatch kwargs mock parameters such as ``return_value``, `side_effect`,
            `spec`, `new_callable`, `mock_configure` and so on.

        _patch: (_Patch):
            Mocker `_patch` wrapper to the ``mock.patch`` features.

        _mock: (_TMockType):
            Mock instance keeper.

        is_active: (bool):
            Flag to sinalize that mock is active. When set to False mock will be cleaned up after
            tested function finished.

    """
    target_path: str = None
    is_async: bool = False
    patch_kwargs: MockMetadataKwargsType = field(default_factory=lambda: {})
    _patch: _Patch = None
    _mock: _TMockType = None
    is_active: bool = False

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
    def mock_configure(self) -> MockMetadataKwargsType:
        return self.patch_kwargs.get('mock_configure')

    @mock_configure.setter
    def mock_configure(self, data: MockMetadataKwargsType):
        self.patch_kwargs['mock_configure'] = data

    @property
    def new(self) -> TypeNew:
        return self.patch_kwargs.get('new')

    @property
    def create(self) -> bool:
        return self.patch_kwargs.get('create')

    @property
    def new_callable(self) -> NewCallableType:
        return self.patch_kwargs.get('new_callable')


try:
    import asyncio

    def _asyncio_future(result: Any) -> asyncio.Future:
        """Function called when patching async ``return_value``.

        Args:
            result (Any):
                Data defined when setting ``patch(return_value)``

        Returns:
            asyncio.Future: Asyncio future Task.
        """
        future = asyncio.Future()
        future.set_result(result)
        return future
except ImportError:
    pass


class Patcher:
    """Patch wrapper for the mocker.patch feature.

    Args:
        _mocker (MockFixture):
            mocker fixture keeper.

        _mocked_metadata (List[TMockMetadata]):
            Instances of patched mocks.
    """
    _mocker: MockFixture = None
    _mocked_metadata: List[TMockMetadata] = []

    @staticmethod
    def dispatch(mock_metadata: TMockMetadata) -> TMocker.PatchType:
        """Our mock patch to properly identify and setting mock properties. We start the mock so we
        can manage state when stopping or restarting mocks and setting results
        (changing ``return_value`` or ``side_effect`` patch properties).

        Args:
            mock_metadata (TMockMetadata):
                Mock metadata instance with mock's data.

        Returns:
            TMocker.PatchType:
                Our Mock Patch Type wrapper.
        """
        if mock_metadata.is_async:
            mock_metadata.return_value = _asyncio_future(
                mock_metadata.return_value
            )
            _side_effect = mock_metadata.side_effect
            if _side_effect:
                if isinstance(_side_effect, list):
                    futures = []
                    for call in _side_effect:
                        futures.append(
                            _asyncio_future(call)
                        )
                    _side_effect = futures
                else:
                    _side_effect = _asyncio_future(_side_effect)
                mock_metadata.side_effect = _side_effect

        if mock_metadata.is_active:
            mock_metadata._mock.configure_mock(
                return_value=mock_metadata.return_value,
                side_effect=mock_metadata.side_effect
            )
            return TMocker.PatchType(
                mock_metadata
            )

        _patch = Patcher._mocker.mock_module.patch(
            mock_metadata.target_path,
            **mock_metadata.patch_kwargs
        )
        _mocked = _patch.start()
        if (not mock_metadata.new) and (not mock_metadata.new_callable):
            _mocked.mock_add_spec(spec=Type[_TMockType])
        mock_metadata.is_active = True
        Patcher._mocker._patches.append(_patch)
        mock_metadata._patch = _patch
        mock_metadata._mock = _mocked
        Patcher._mocked_metadata.append(mock_metadata)

        if hasattr(_mocked, "reset_mock"):
            Patcher._mocker._mocks.append(_mocked)

        _tmock_patch = TMocker.PatchType(
            mock_metadata
        )
        return _tmock_patch

    @staticmethod
    def _clean_up():
        """Our way to clean up patched data from mocker fixture."""
        print("\n######################## cleaning up ########################")
        for mock_metadata in Patcher._mocked_metadata:
            if not mock_metadata.is_active:
                try:
                    Patcher._mocker._patches.remove(mock_metadata._patch)
                except ValueError:
                    print("Opss!", mock_metadata._patch, "Not found!")
                    pass
        del Patcher._mocked_metadata[:]


@dataclass
class TMockMetadataBuilder:
    """Here we build our mock metada to parse mock parameters and propagate state.

    Args:
        _mock_metadata (TMockMetadata):
            Mock metadata instance to propagate mock state.

        _mock_keys_validate (List[str]):
            Mock parameters we need to check if were setted to dispatch to ``mock.patch`` creation.

        _bypass_methods (List[str]):
            Methods we need keeping properly behavior for return value.

    Raises:
        MockerBuilderException:
            Notify users when we found in trouble.

    """
    _mock_metadata: TMockMetadata = None
    _mock_keys_validate: List[str] = field(default_factory=lambda: [
        'new',
        'spec',
        'create',
        'spec_set',
        'autospec',
        'new_callable',
        'return_value',
        'side_effect',
        'mock_configure',
        'mock_kwargs'
    ])
    _bypass_methods: List[str] = field(default_factory=lambda: [
        '__init__'
    ])

    def __mock_kwargs_builder(
        self,
        mock_metadata_kwargs: MockMetadataKwargsType
    ):
        kwargs = {}
        for attr in self._mock_keys_validate:
            value = mock_metadata_kwargs.get(attr)
            if value:
                if isinstance(value, dict):
                    for key, data in value.items():
                        kwargs.update({key: data})
                    continue
                kwargs.update({attr: value})
        self._mock_metadata.patch_kwargs = kwargs

    def __apply_bypass_methods_return_value(self):
        if self._mock_metadata.target_path.rsplit('.', 1)[-1] in self._bypass_methods:
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
            MockerBuilderException:
                Notify users when we found in trouble.

        Returns:
            TMockMetadata:
                Mock metadata to keep mock and patch state and creation.
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
            # Here we parse the target parameter to identify the type and spliting by
            # package/module, module, class and method or attribute we are going to mock converting
            # the path to string.
            attr = method if method else attribute if attribute else None
            if inspect.isclass(target):
                _target_path = tuple(filter(None, [
                    target.__module__,
                    target.__name__,
                    attr
                ]))
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
            elif inspect.isdatadescriptor(target):
                raise MockerBuilderException(
                    "### Sorry, but in the moment we are not prepared "
                    "to deal with @property type mocking like that yet ###"
                )
            elif isinstance(target, object):
                _target_path = tuple(filter(None, [
                    target.__module__,
                    type(target).__name__,
                    attr
                ]))
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
            self._mock_metadata = TMockMetadata()
            self._mock_metadata.target_path = mock_target_path
            self.__mock_kwargs_builder(kwargs)
            self.__apply_bypass_methods_return_value()
            check_mock_target = self.__load_safe_mock_target_path_from_module(_target_path)
            if inspect.iscoroutinefunction(check_mock_target):
                self._mock_metadata.is_async = True

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
                try:
                    module_attr = getattr(module, attr)
                    if module_attr:
                        return module_attr
                    return module
                except AttributeError as ex:
                    if self._mock_metadata.create:
                        return module
                    raise MockerBuilderException(ex)

            module = import_module(module_path)
            is_klass = getattr(module, klass_or_module)
            if inspect.isclass(is_klass):
                try:
                    klass_attr = getattr(is_klass, attr)
                    if klass_attr:
                        return klass_attr
                    return is_klass
                except AttributeError as ex:
                    if self._mock_metadata.create:
                        return is_klass
                    raise MockerBuilderException(ex)

            is_module = getattr(module, klass_or_module)
            if inspect.ismodule(is_module):
                try:
                    module_attr = getattr(is_module, attr)
                    if module_attr:
                        return module_attr
                    return is_module
                except AttributeError as ex:
                    if self._mock_metadata.create:
                        return is_module
                    raise MockerBuilderException(ex)
        except Exception as ex:
            raise MockerBuilderException(ex)


class TMocker:
    """Our API to handle patch and mock features"""

    @staticmethod
    def _patch(
        mock_metadata: TMockMetadata
    ) -> TMocker.PatchType:
        return Patcher.dispatch(mock_metadata)

    @dataclass(init=False)
    class _TPatch(Generic[_TMockType]):
        """Our specialized Mock to handle with MagicMock or AsyncMock types.

        Args:
            Generic (_TMockType):
                Mock type we give back to user's tests.

            mock_metadata (TMockMetadata):
                Mock metadata instance given from `TMockMetadataBuilder`.
        """
        __mock_metadata: TMockMetadata = None

        def __init__(self, mock_metadata: TMockMetadata) -> None:
            self.__mock_metadata = mock_metadata

        @property
        def mock(self) -> MockType:
            return self.__get_mock()

        def __call__(self) -> MockType:
            return self.__get_mock()

        def __enter__(self) -> MockType:
            return self.__get_mock()

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.stop()

        def __get_mock(self) -> _TMockType:
            return self.__mock_metadata._mock

        def set_result(
            self,
            return_value: ReturnValueType = None,
            side_effect: SideEffectType = None
        ):
            # TODO Let's think how to allow conditional setting return_value and/or side_effect.
            # Ex: return_value = foo if foo else buu
            self.__mock_metadata.return_value = return_value
            self.__mock_metadata.side_effect = side_effect
            _tpath = Patcher.dispatch(
                self.__mock_metadata
            )
            self.__mock_metadata = _tpath.__mock_metadata

        def start(self):
            self.__mock_metadata._mock = self.__mock_metadata._patch.start()
            self.__mock_metadata.is_active = True
            print(f"Mock {self.__get_mock()} started")

        def stop(self):
            self.__mock_metadata._patch.stop()
            self.__mock_metadata.is_active = False
            print(f"Mock {self.__get_mock()} stopped")

    PatchType = _TPatch[_TMockType]


TFixtureContentType = TypeVar('TFixtureContentType')


class MockerBuilder(ABC):
    """Our interface to connect mock metadata builder to the user's building tests"""

    def initializer(fnc):
        @pytest.fixture(autouse=True)
        def builder(test_main_class, mocker: MockFixture):
            """Decorator which inject a fixture to the TestClass method decorated with this
            so we can get the mocker fixture injected to be used all spread on the tests.

            Args:
                test_main_class:
                    The pytest main TestClass which runs all tests.

                mocker:
                    pytest-mock fixture to create patch and so on.
            """
            print("\n################# Mocker Builder Initializer ################")
            Patcher._mocker = mocker
            setattr(test_main_class, 'mocker', mocker)
            yield fnc(test_main_class)

            # Cleaning up stopped mocks: mock_metadata.is_active = False to avoid raising
            # mocker RuntimeError: "stop called on unstarted patcher".
            Patcher._clean_up()
        return builder

    @abstractmethod
    def mocker_builder_setup(self):
        """Method to setup your tests initializing mocker builder features.

        .. code-block:
            :caption: Example
                TestYourClassOfTests(MockerBuilder):

                    @MockerBuilder.initializer
                    def mocker_builder_setup(self):
                        self = my_desired_mock = self.patch(...)

        """
        raise NotImplementedError("Please, implement me!")

    def patch(
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
        mock_configure: MockMetadataKwargsType = None,
        **kwargs
    ) -> TMocker.PatchType:
        """From here we create new ``mock.patch`` parsing the ``target`` parameter. You can just set
        your target as normal imported class, module or method. You don't need to pass it as string
        like normal ``mock.patch`` does. Here we make it easier by just allowing to set the ``target``
        parameter for classes, modules and methods or functions without the need of setting the
        ``method`` parameter. Just if you wanna mock an attribute you must set it from the
        ``attribute`` parameter as string. The ``target`` can be am imported class or module
        but the ``attribute`` need to be passed as string.

        .. code-block::
            :caption: Test Cases

                from testing_heroes.my_heroes
                import JusticeLeague

                class TestMyHeroes(MockerBuilder):

                    @MockerBuilder.initializer
                    def mocker_builder_setup(self):
                            self.mock_justice_league__init__ = self.patch(
                                target=JusticeLeague.__init__
                            )

                    @pytest.mark.asyncio
                    async def test_heroes_sleeping(self):
                        justce_league = JusticeLeague()
                        assert self.mock_justice_league__init__().called

                        async def hero_names():
                            yield Batman().nickname
                            yield Robin().nickname

                        _hero_names = hero_names()

                        async for result in justce_league.are_heroes_sleeping():
                            assert result == "=== Heroes are awakened ==="

                        self.mock_justice_league__init__.stop()

                        justce_league = JusticeLeague()

                        async for result in justce_league.are_heroes_sleeping():
                            _hero_name = await _hero_names.__anext__()
                            assert result == f"MagicMock=>({_hero_name}): ZZzzzz"

        .. code-block::
           :caption: Types

                TargetType = TypeVar('TargetType', Callable, ModuleType, str)

                AttrType = TypeVar('AttrType', bound=Union[Callable, str])

                TypeNew = TypeVar('TypeNew', bound=Any)

                NewCallableType = TypeVar('NewCallableType', bound=Optional[Callable])

                ReturnValueType = TypeVar('ReturnValueType', bound=Optional[Any])

                SideEffectType = TypeVar('SideEffectType', bound=Optional[Union[Callable, List]])


        .. note::
            This doc is defined in unittest.patch doc. For a complete documentation please see:
            https://docs.python.org/3/library/unittest.mock.html#the-patchers

        Args:
            target (TargetType):
                The target to be mocked.

            method (AttrType[str], optional):
                Method to be mocked, useful when need to create an method or dynamically invoking.

            attribute (AttrType[str], optional):
                Attribute to be mocked. Defaults to None.

            new (TypeNew, optional):
                The new type that ``target`` attribute will get after mocking.
                Defaults to DEFAULT.

                .. code-block:
                    :caption: Example

                        self.patch(
                            target=MyClass,
                            attribute='my_class_attr',
                            new=PropertyMock(OtherClass)
                        )

            spec (bool, optional):
                This can be either a list of strings or an existing object (a
                class or instance) that acts as the specification for the mock object. If
                you pass in an object then a list of strings is formed by calling dir on
                the object (excluding unsupported magic attributes and methods). Accessing
                any attribute not in this list will raise an ``AttributeError``.

                If ``spec`` is an object (rather than a list of strings) then
                ``mock.__class__`` returns the class of the spec object. This allows mocks to pass
                `isinstance` tests.

            create (bool, optional):
                By default patch() will fail to replace
                attributes that don't exist. If you pass in create=True, and the attribute doesn't
                exist, patch will create the attribute for you when the patched function is called,
                and delete it again after the patched function has exited. This is useful
                for writing tests against attributes that your production code creates at runtime.
                It is off by default because it can be dangerous. With it switched on you can write
                passing tests against APIs that don't actually exist!.

            spec_set (bool, optional):
                A stricter variant of ``spec``. If used, attempting to *set*
                or get an attribute on the mock that isn't on the object passed as
                `spec_set` will raise an `AttributeError`.

            autospec (Union[bool, Callable], optional):
                A more powerful form of spec is autospec.
                If you set autospec=True then the mock will be created with a spec from the object
                being replaced. All attributes of the mock will also have the spec of the corresponding
                attribute of the object being replaced. Methods and functions being mocked will have
                their arguments checked and will raise a TypeError if they are called with the wrong
                signature. For mocks replacing a class, their return value (the 'instance') will have
                the same spec as the class. See the create_autospec() function and Autospeccing.

                Instead of autospec=True you can pass autospec=some_object to use an arbitrary object
                as the spec instead of the one being replaced.

            new_callable (NewCallableType, optional):
                Allows you to specify a different class,
                or callable object, that will be called to create the new object.
                By default AsyncMock is used for async functions and MagicMock for the rest.

            return_value (ReturnValueType, optional):
                The value returned when the mock is called. By default this is a new Mock
                (created on first access). See the `return_value` attribute.

            side_effect (SideEffectType, optional):
                A function to be called whenever the Mock is called. See the ``side_effect``
                attribute. Useful for raising exceptions or dynamically changing return values.
                The function is called with the same arguments as the mock, and unless it returns
                ``DEFAULT``, the return value of this function is used as the return value.

                If `side_effect` is an iterable then each call to the mock will return
                the next value from the iterable. If any of the members of the iterable
                are exceptions they will be raised instead of returned.

            mock_configure (MockMetadataKwargsType, optional):
                Set attributes on the mock through keyword arguments. It exists to make it easier
                to do configuration after the mock has been created.

                Attributes plus return values and side effects can be set on child mocks using
                standard dot notation::

                    mock_who_is_my_hero = self.patch(
                        target=Batman,
                        mock_configure={
                            'return_value.nickname': 'Bat Mock',
                            'return_value.eating_banana.return_value': "doesn't like banana",
                            'return_value.wearing_pyjama.return_value': "doesn't wear pyjama",
                            'return_value.just_call_for.return_value': "Just calls for Mocker",
                            'return_value.just_says.return_value': "I'm gonna mock you babe!",
                        }
                    )

        Returns:
            TMocker.PatchType:
                Alias to _TPatch Generics which handle with MagicMock or AsyncMock
                (not yet really but working on) according patching async methods or not.
        """
        return TMocker._patch(
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
                mock_configure=mock_configure,
                mock_kwargs=kwargs
            )
        )

    def add_fixture(
        self,
        content: TFixtureContentType,
    ) -> TFixtureContentType:
        """Method to simulate a pytest fixture to be called in every test but in another way.

        Args:
            content (TFixtureContentType):
                Method to be called and returned or yielded

        Returns:
            TFixtureContentType:
                The return/yield data from content.

        """
        if callable(content):
            result = content()
        else:
            result = content
        if inspect.isgenerator(result):
            return next(result)
        else:
            return result
