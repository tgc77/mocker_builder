from dataclasses import dataclass
from io import StringIO
from typing import Union
from unittest.mock import MagicMock
import pytest

from mocker_builder import MockerBuilder
from testing_heroes import my_heroes
from testing_heroes.my_heroes import Batman, FakeHero, IHero, PeakyBlinder, Robin, TestingHeroes, who_is_my_hero


def foo():
    print("Something")


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
        # ==================== Works ======================
        # self.add_mock(
        #     mock_name="mock_test_io",
        #     target='sys.stdout',
        #     new_callable=StringIO
        # )

        self.add_mock(
            mock_name="mock_testing_heroes_class",
            target=TestingHeroes
        )
        # =================================================

        self.add_mock(
            mock_name="mock_my_heroes_module",
            target=my_heroes.initialize_other_hero,
            # autospec=True
        )

        # self.add_mock(
        #     mock_name='mock_my_hero',
        #     target=TestingHeroes._my_hero,
        #     **{
        #         'method.return_value': 3,
        #         'other.side_effect': KeyError
        #     }
        # )
        self.mocker_builder_start()

    def est_io(self):
        foo()
        assert self.mock_test_io.getvalue() == 'Something\n'

    def test_mock_testing_heroes_class(self):
        my_heroes.who_is_the_best_hero()

        assert self.mock_testing_heroes_class.called

    def est_mock_my_heroes_module(self):
        # my_heroes.who_is_the_best_hero()

        # assert not self.mock_my_heroes_module.initialize_other_hero.called
        assert self.mock_my_heroes_module.called

    def est_my_hero(self):
        pass
        # assert self.mock_object.method() == 3
        # with pytest.raises(KeyError) as err:
        #     assert self.mock_object.other() == err

        # def _side_effect(my_hero: IHero):
        #     ...
        # ========= settimg mocks
        # self.add_mock(
        #     mock_name='mock_who_is_my_hero',
        #     target=my_heroes.who_is_my_hero,
        #     return_value="I have no hero, mate!"
        # )

        # self.add_mock(
        #     mock_name='mock_my_hero__call__',
        #     target=TestingHeroes.__call__,
        #     side_effect=lambda _my_hero: Robin()
        # )

        # TODO this test passed but looks wird the configure_mock
        # self.add_mock(
        #     mock_name='mock_my_hero',
        #     target=TestingHeroes,
        #     attribute='_my_hero',
        #     **{
        #         # '_my_hero': Robin(),
        #         '_my_hero.eating_banana': "No No No banana!",
        #         '_my_hero.just_says': "I have nothing to say!"
        #     }
        # )

        # self.add_mock(
        #     mock_name='mock_my_hero_II',
        #     target=TestingHeroes,
        #     method='just_says',
        #     return_value="Just says: Ops! I have been mocked too!",
        # )

        # self.add_mock(
        #     mock_name='mock_the_best_hero',
        #     target=my_heroes,
        #     attribute='THE_BEST_HERO',
        #     new=Batman(),
        # )

        # self.add_mock(
        #     mock_name='mock_other_hero',
        #     target=my_heroes.OTHER_HERO,
        #     new=Robin(),
        # )

    @pytest.mark.asyncio
    async def est_my_heroes(self):
        print("The best hero before mocker start:")
        my_heroes.who_is_the_best_hero()

        self.mocker_builder_start()

        print("The best hero after mocker start:")
        my_heroes.who_is_the_best_hero()

        # print(
        #     "Who is my hero?",
        #     my_heroes.who_is_my_hero()
        # )

        # testing_code = TestingHeroes()(self.my_hero)

        # assert testing_code.just_says() == "Just says: Ops! I have been mocked!"
        # assert self.mock_my_hero.called

        # TODO check if need to inject params to the mock
        # perhaps should create keyword configure_mock to accept
        # a dict config {'_my_hero.just_says'}
        # self.mock_my_hero.says()

        # assert testing_code._my_hero.bananas == 12
        # assert testing_code._my_hero.pyjamas == 7
        # assert testing_code._my_hero.nickname == "Bellboy"

        # ('testing_heroes.my_heroes.who_is_my_hero', '')
        # ('testing_heroes.my_heroes', 'who_is_my_hero')

        # ('testing_heroes.my_heroes', 'who_is_my_hero')
        # ('testing_heroes', 'my_heroes')

        # ('testing_heroes.my_heroes.TestingHeroes.just_says', '')
        # ('testing_heroes.my_heroes.TestingHeroes', 'just_says')

        # ('testing_heroes.my_heroes.TestingHeroes', 'just_says')
        # ('testing_heroes.my_heroes', 'TestingHeroes')
