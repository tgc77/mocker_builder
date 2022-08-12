from dataclasses import dataclass
from typing import Union
import pytest

from mocker_builder import MockerBuilder


@dataclass
class FakeUser:
    id = 2
    cpf = '12345678911'
    email = 'teste@teste.com'

    def to_dict(self):
        return {
            'id': self.id,
            'cpf': self.cpf,
            'email': self.email
        }


@dataclass
class MyFixture:
    cpf: str = None
    email: str = None


@dataclass
class Batman:
    a: int = 1
    b: int = 2

    def racking_you(self):
        print(f"{self.__class__.__name__} Can I rack you?")

    def another_func(self):
        print(f"{self.__class__.__name__} Hi there! I'am another func!")

    def show_my_klass(self):
        print(self.__dict__)


@dataclass
class SpyderMan:
    a: int = 3
    b: int = 4

    def racking_you(self):
        print(f"{self.__class__.__name__} Can I rack you?")

    def another_func(self):
        print(f"{self.__class__.__name__} Hi there! I'am another func!")

    def show_my_klass(self):
        print(self.__dict__)


class TestingCode:
    _my_klass: Union[Batman, SpyderMan] = None

    def racking_you(self):
        self._my_klass.racking_you()

    def another_func(self):
        self._my_klass.another_func()

    def show_my_klass(self):
        self._my_klass.show_my_klass()

    def func_call_test(self):
        try:
            self.func_test()
        except Exception as e:
            print(f"Opps2! {e}")
            try:
                self._my_klass.func_test()
            except Exception as e:
                print(f"Opps3! {e}")


class TestMockerBuilder(MockerBuilder):

    @MockerBuilder.initializer
    def mocker_builder_initializer(self):
        print("######################### initializer #################################")
        # ========= setting fixtures
        self.fixture_register(
            name="my_fixture",
            return_value=MyFixture(
                cpf='12345678901',
                email='teste@teste.bla'
            )
        )

        async def _side_effect(*args, **kwargs):
            # print("Testing side_effect returning DEFAULT")
            # return DEFAULT
            class Fake:
                async def get(self, **kwargs):
                    return FakeUser()
            return Fake()

        # ========= settimg mocks
        self.add_mock(
            mock_name='mock_testing_code',
            klass=TestingCode,
            attribute='_my_klass',
            # new=Batman(),
            # new_callable=MagicMock(Batman),
            # spec=Batman(),
            func_test=lambda: print('ouieeeeh!'),
            return_value=Batman(),
            # autospec=True,
            # side_effect=_side_effect
        )

    @pytest.mark.asyncio
    async def test_execute_success(self):
        self.mocker_builder_start()

        testing_code = TestingCode()
        try:
            self.mock_testing_code.func_test()
        except Exception as e:
            print(f"Eita! {e}")

        testing_code.func_call_test()

        testing_code.racking_you()
        testing_code.another_func()
        testing_code.show_my_klass()

        assert self.my_fixture.cpf == "12345678901"
        assert self.my_fixture.email == 'teste@teste.bla'
