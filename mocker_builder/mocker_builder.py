from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass, field
from pprint import pprint
from typing import Any, Callable, Dict, List, TypeVar, Union
import inspect
from unittest.mock import DEFAULT, MagicMock
import pytest
from pytest_mock import MockerFixture
from pytest_mock.plugin import AsyncMockType

Tk = TypeVar('Tk', bound=Callable)
Tv = TypeVar('Tv')
Tr = TypeVar('Tr')
Tse = TypeVar('Tse', Callable, List)

__version__ = "0.1.0"


# TODO remover esta função e limpar libs não utilizadas
def dict_print(message, data):
    print(message)
    pprint(data, indent=4)
    # print(json.loads(json.dumps(data, sort_keys=True, indent=4)))
    # print(yaml.dump(data, default_flow_style=False))


class MockerBuilderError(Exception):
    """ Error in MockerBuilder usage or invocation"""


@dataclass
class MockMetadata:
    mock_name: str
    klass: Tk = None
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


class MockerBuilderImpl:
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
        self._test_main_class = None

    def _register_test_main_class(self, t_main_class: Tk):
        self._test_main_class = t_main_class

    def _start(self):
        self.__load_metadata()

    def _mock_kwargs_builder(self, mock_metadata: MockMetadata) -> Dict[str, Any]:
        kwargs = {}
        for attr in self.__mock_keys_validate:
            valeu = getattr(mock_metadata, attr)
            if valeu:
                kwargs.update({attr: valeu})
        return kwargs

    def patcher(self, mock_metadata: MockMetadata) -> Union[MagicMock, AsyncMockType]:
        method = mock_metadata.method
        attribute = mock_metadata.attribute
        klass = mock_metadata.klass
        _args = [method if method else attribute]
        _kwargs = self._mock_kwargs_builder(mock_metadata)

        # TODO: testar se é possível utilizar um modulo em vez de uma classe para
        if klass:
            return self._mocker.patch.object(
                klass,  # poderia ser um modulo aqui?
                *_args,
                **_kwargs
            )
        # if klass else self._mocker(
        #     *args,
        #     **kwargs
        # )

    def __load_safe_mock_param_path_from_module(self, safe_method: str):
        from importlib import import_module
        path, func = safe_method.rsplit('.', 1)
        module, klass = path.rsplit('.', 1)
        is_class = getattr(import_module(module), klass)

        if inspect.isclass(is_class):
            return getattr(is_class, func)

        return getattr(import_module(path), func)

    # TODO: implementar patch.dict para reconhecer quando target for um dict
    # ver se fica melhor fazer essa validação do patch na classe _Mocker para tirar daqui

    def __patch(
        self,
        mock_metadata: MockMetadata
    ):
        mock_name = mock_metadata.mock_name
        klass = mock_metadata.klass
        method = mock_metadata.method
        attribute = mock_metadata.attribute
        return_value = mock_metadata.return_value
        side_effect = mock_metadata.side_effect

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

        mock_param_path = ".".join(
            [klass.__module__, klass.__name__, method if method else attribute]
        ) if klass else method
        try:
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
            # TODO remover os prints e adicionar logs e ativar raise
            print(f"#__patch: Oops! {ex}")
            # raise MockerBuilderError(ex)

    def _add_mock(self, mock_metadata: MockMetadata):
        self._mock_metadata.update({
            mock_metadata.mock_name: mock_metadata
        })

    def __load_metadata(self):
        for _, mock_metadata in self._mock_metadata.items():
            if not mock_metadata.active:
                continue

            self.__patch(
                mock_metadata
            )

    # TODO: Verificar quais destes métodos vão precisar pois agora temos acesso aos
    # dados do mocker: _Mocker
    def _set_mock_method_return_value(self, mock_method: str, return_value: Tr):
        self._mock_metadata.get(mock_method)['return_value'] = return_value

    def _activate_mock_method(self, mock_method: str):
        self._mock_metadata.get(mock_method)['active'] = True

    def _deactivate_mock_method(self, mock_method: str):
        self._mock_metadata.get(mock_method)['active'] = False

    def _get_mocked_method(self, mock_method: str) -> Any:
        return self._mocked_method.get(mock_method)


class IMockerBuilder(ABC):
    __mocker_builder: MockerBuilderImpl = None
    __fixtures: Dict = {}

    def initializer(fnc):
        @pytest.fixture(autouse=True)
        def builder(test_main_class, mocker):
            print("\n##################### mocker_builder_create #######################")
            IMockerBuilder.__mocker_builder = MockerBuilderImpl(mocker)
            IMockerBuilder.__mocker_builder._register_test_main_class(test_main_class)
            yield fnc(test_main_class)
            # print("\n############# need to run gc.collect() or clean memory ? ##############")
        return builder

    @abstractmethod
    def mocker_builder_initializer(self):
        pass

    def fixture_register(self, name, return_value):
        self.__fixtures.update({
            name: return_value
        })
        setattr(self, name, return_value)

    def add_mock(
        self,
        mock_name: str,
        klass: Tk = None,
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
            klass=klass,
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

    def mocker_builder_start(self):
        self.__mocker_builder._start()

    # TODO: refactor all thise methods
    def set_mock_method_return_value(self, mock_method: str, return_value: Tr):
        self.__mocker_builder._set_mock_method_return_value(mock_method, return_value)

    def activate_mock_method(self, mock_method: str):
        self.__mocker_builder._activate_mock_method(mock_method)

    def deactivate_mock_method(self, mock_method: str):
        self.__mocker_builder._deactivate_mock_method(mock_method)

    def get_mocked_method(self, mock_method: str) -> Any:
        return self.__mocker_builder._get_mocked_method(mock_method)
