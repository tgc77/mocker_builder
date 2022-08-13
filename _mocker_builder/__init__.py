from abc import ABC, abstractmethod
import asyncio
from collections import OrderedDict
from pprint import pprint
from typing import Any, Callable, Dict, List, TypeVar, Union
import inspect
from unittest.mock import DEFAULT
import pytest
from pytest_mock import MockFixture

Tk = TypeVar('Tk', bound=Callable)
Tv = TypeVar('Tv')
Tr = TypeVar('Tr')
Tse = TypeVar('Tse', Callable, List)

__version__ = "0.1.0"


class MockerBuilderError(Exception):
    """ Error in MockerBuilder usage or invocation"""


# TODO remover esta função e limpar libs não utilizadas
def dict_print(message, data: OrderedDict):
    print(message)
    pprint(data, indent=4)
    # print(json.loads(json.dumps(data, sort_keys=True, indent=4)))
    # print(yaml.dump(data, default_flow_style=False))


class _Mocker(MockFixture):
    def patcher(self, *args):
        pass


class MockerBuilderImpl:
    __mock_validate_keys = [
        'new',
        'spec',
        'create',
        'spec_set',
        'autospec',
        'new_callable',
        'return_value',
        'side_effect'
    ]

    def __init__(self, mocker: _Mocker) -> None:
        self._mocker = mocker
        self._mocked_method = {}
        # Dict[str, Union[MagicMock, AsyncMock]]
        self._mock_metadata = {}
        self._test_main_class = None

    def _register_test_main_class(self, t_main_class: Tk):
        self._test_main_class = t_main_class

    def _start(self):
        self.__load_metadata()

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
        mock_name: str,
        **kwargs: OrderedDict
    ):
        klass = kwargs.pop('klass')
        method = kwargs.pop('method')
        attribute = kwargs.pop('attribute')
        kwargs.pop('active')

        # dict_print("#########__patch -> kwargs: ", kwargs)

        for key in self.__mock_validate_keys:
            if not kwargs.get(key):
                kwargs.pop(key)

        return_value = kwargs.get('return_value')
        side_effect = kwargs.get('side_effect')

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
                kwargs['return_value'] = future
                # TODO: Implementar return_value e/ou side_effect condicional Ex if result:...
                # TODO testar usar side_effect com future...
        except Exception as e:
            # TODO remover os prints e adicionar logs e ativar raise
            # raise MockerBuilderError(f"Eita! {e}")
            print(f"Eita! {e}")

        # TODO: substituir esta func chamando _Mocker.patcher(*args, **kwargs)
        def mocker_patch(klass: Tk):
            # TODO if return_valeu keyword exists we can pass kwargs ???

            # TODO: testar substituir a keyword new= por um args e pesquisar a utilização
            # e comportamento do new.
            func_params = [
                method if method else attribute, kwargs
            ]
            # print(f"######### mocker_patch -> func_params:\n {func_params}")

            # TODO: testar se é possível utilizar um modulo em vez de uma classe para
            return self._mocker.patch.object(
                klass,  # poderia ser um modulo aqui?
                func_params[0],
                **func_params[1]
            )
            # if klass else self._mocker(
            #     *func_params[0],
            #     **func_params[1]
            # )
        try:
            self._mocked_method[mock_name] = mocker_patch(klass)
            if kwargs.get('new') == DEFAULT:
                self._mocked_method[mock_name].configure_mock(**kwargs.get('kwargs', {}))
            setattr(self._test_main_class, mock_name, self._mocked_method[mock_name])
        except Exception as ex:
            # TODO remover os prints e adicionar logs e ativar raise
            print(f"Oopsssss! {ex}")
            # raise MockerBuilderError(ex)

    def _add_mock(
        self,
        mock_name: str,
        **kwargs: OrderedDict
    ):
        self._mock_metadata.update({
            mock_name: {
                **kwargs
            }
        })

    def __load_metadata(self):
        for mock_name, mock_params in self._mock_metadata.items():
            if not bool(mock_params.get('active')):
                continue

            self.__patch(
                mock_name=mock_name,
                **mock_params
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
            # print("\n############### need to run gc.collect() or clean memory ? ################")
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
        mock_params = OrderedDict([
            ('klass', klass),
            ('method', method),
            ('attribute', attribute),
            ('new', new),
            ('spec', spec),
            ('create', create),
            ('spec_set', spec_set),
            ('autospec', autospec),
            ('new_callable', new_callable),
            ('return_value', return_value),
            ('side_effect', side_effect),
            ('active', active)
        ])
        mock_params.update([('kwargs', kwargs)]) if kwargs else None
        self.__mocker_builder._add_mock(
            mock_name=mock_name,
            **mock_params
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
