from dataclasses import dataclass
from typing import Union
from unittest.mock import MagicMock
import pytest

from mocker_builder import MockerBuilder
from testing_heroes.my_heroes import Batman, FakeHero, MyHero, TestingHeroes


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
    async def test_my_heroes(self):
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
