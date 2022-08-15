from dataclasses import dataclass
from typing import Union
import pytest

from mocker_builder import MockerBuilder


@dataclass
class FakeHero:
    bananas: int = 2
    pyjamas: int = 2
    nickname: str = 'Bad Fat Hero'

    def to_dict(self):
        return {
            'bananas': self.bananas,
            'pyjamas': self.pyjamas,
            'nickname': self.nickname
        }


@dataclass
class MyHero:
    bananas: int = 3
    pyjamas: int = 2
    nickname: str = "Harry Potter"


@dataclass
class Batman:
    bananas: int = 1
    pyjamas: int = 2
    nickname: str = "Big Fat Bat"

    def eating_banana(self):
        print(f"{self.__class__.__name__} are eating {self.bananas} banana(s)!")

    def wearing_pyjama(self):
        print(f"{self.__class__.__name__} are wearing {self.pyjamas} pyjama(s)!")

    def just_call_for(self):
        print(f"My hero just call for {self.nickname}")

    def just_says(self):
        print(f"{self.__class__.__name__} just says: HUEHUEHUEH")


@dataclass
class Robin:
    bananas: int = 3
    pyjamas: int = 4
    nickname: str = "Little Bastard"

    def eating_banana(self):
        print(f"{self.__class__.__name__} are eating {self.bananas} banana(s)!")

    def wearing_pyjama(self):
        print(f"{self.__class__.__name__} are wearing {self.pyjamas} pyjama(s)!")

    def just_call_for(self):
        print(f"My hero just call for {self.nickname}")

    def just_says(self):
        print(f"{self.__class__.__name__} just says: kkkkkkkkkk")


class TestingHeroes:
    _my_hero: Union[Batman, Robin] = None

    def eating_banana(self):
        self._my_hero.eating_banana()

    def wearing_pyjama(self):
        self._my_hero.wearing_pyjama()

    def just_call_for(self):
        self._my_hero.just_call_for()

    def my_hero_just_says(self):
        try:
            self.just_says()
        except Exception as e:
            print(f"OpsII! {e}")
            try:
                self._my_hero.just_says()
            except Exception as e:
                print(f"OpsIII! {e}")


class TestMockerBuilder(MockerBuilder):

    @MockerBuilder.initializer
    def mocker_builder_initializer(self):
        print("######################### initializer #######################")
        # ========= setting fixtures
        self.fixture_register(
            name="my_hero",
            return_value=MyHero(
                bananas=12,
                pyjamas=7,
                nickname="Bellboy"
            )
        )

        async def _side_effect(*args, **kwargs):
            class Fake:
                async def get(self, **kwargs):
                    return FakeHero()
            return Fake()

        # ========= settimg mocks
        self.add_mock(
            mock_name='mock_testing_heroes',
            klass=TestingHeroes,
            attribute='_my_hero',
            new=Batman(),
            # new_callable=MagicMock(Batman),
            # spec=Batman(),
            just_says=lambda: print('ouieeeeh!'),
            # return_value=Batman(),
            # autospec=True,
            # side_effect=_side_effect
        )

    @pytest.mark.asyncio
    async def test_execute_success(self):
        self.mocker_builder_start()

        testing_code = TestingHeroes()
        try:
            self.mock_testing_heroes.just_says()
        except Exception as e:
            print(f"Eita! {e}")

        testing_code.my_hero_just_says()

        testing_code.eating_banana()
        testing_code.wearing_pyjama()
        testing_code.just_call_for()

        assert self.my_hero.bananas == 12
        assert self.my_hero.pyjamas == 7
        assert self.my_hero.nickname == "Bellboy"
