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
            mock_name='mock_my_hero',
            target=TestingHeroes,
            # TODO try mock a _my_hero.just_says
            # attribute='_my_hero',
            method='just_says',
            # new=Batman(),
            # new_callable=MagicMock(Batman),
            # spec=Batman(),
            says=lambda: print('ouieeeeh!'),
            return_value="Ops! I have been mocked!",
            # autospec=True,
            # side_effect=_side_effect
        )

        self.add_mock(
            mock_name='mock_the_best_hero',
            target=my_heroes,
            attribute='THE_BEST_HERO',
            new=Batman(),
        )

        # self.add_mock(
        #     mock_name='mock_who_is_the_best_hero',
        #     target=my_heroes,
        #     method='who_is_the_best_hero',
        #     return_value="I'm my best hero!",
        # )

    @pytest.mark.asyncio
    async def test_my_heroes(self):
        print("The best hero before mocker start:")
        my_heroes.who_is_the_best_hero()

        self.mocker_builder_start()

        print("The best hero after mocker start:")
        my_heroes.who_is_the_best_hero()

        testing_code = TestingHeroes()(self.my_hero)

        assert testing_code.just_says() == "Ops! I have been mocked!"
        assert self.mock_my_hero.called

        # TODO check if need to inject params to the mock
        # perhaps should create keyword configure_mock to accept
        # a dict config {'_my_hero.just_says'}
        self.mock_my_hero.says()

        assert testing_code._my_hero.bananas == 12
        assert testing_code._my_hero.pyjamas == 7
        assert testing_code._my_hero.nickname == "Bellboy"
