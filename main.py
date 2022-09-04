from dataclasses import dataclass
from typing import Union
from unittest.mock import MagicMock
import pytest

from mocker_builder import MockerBuilder
from testing_heroes import my_heroes
from testing_heroes.my_heroes import Batman, FakeHero, PeakyBlinder, Robin, TestingHeroes


class TestMockerBuilder(MockerBuilder):

    @MockerBuilder.initializer
    def mocker_builder_initializer(self):
        print("######################### initializer #######################")
        # ========= setting fixtures
        self.fixture_register(
            name="my_hero",
            return_value=PeakyBlinder(
                bananas=12,
                pyjamas=7,
                nickname="Bellboy"
            )
        )

        async def _side_effect(*args, **kwargs):
            class Fake:
                async def who_is_my_hero(self):
                    return FakeHero()
            return Fake()

        # ========= settimg mocks
        self.add_mock(
            mock_name='mock_who_is_my_hero',
            target=my_heroes.who_is_my_hero,
            return_value="I have no hero, mate!"
        )
        self.add_mock(
            mock_name='mock_my_hero',
            target=TestingHeroes.just_says,
            says=lambda: print('ouieeeeh!'),
            return_value="Just says: Ops! I have been mocked!",
            **{
                # '_my_hero': Batman(),
                '_my_hero.eating_banana.return_value': "No No No banana!"
            }
        )
        self.add_mock(
            mock_name='mock_the_best_hero',
            target=my_heroes,
            attribute='THE_BEST_HERO',
            new=Batman(),
        )

    @pytest.mark.asyncio
    async def test_my_heroes(self):
        print("The best hero before mocker start:")
        my_heroes.who_is_the_best_hero()

        self.mocker_builder_start()

        print("The best hero after mocker start:")
        my_heroes.who_is_the_best_hero()

        print("Who is my hero?")
        my_heroes.who_is_my_hero()

        testing_code = TestingHeroes()(self.my_hero)

        assert testing_code.just_says() == "Just says: Ops! I have been mocked!"
        assert self.mock_my_hero.called

        # TODO check if need to inject params to the mock
        # perhaps should create keyword configure_mock to accept
        # a dict config {'_my_hero.just_says'}
        self.mock_my_hero.says()

        assert testing_code._my_hero.bananas == 12
        assert testing_code._my_hero.pyjamas == 7
        assert testing_code._my_hero.nickname == "Bellboy"
