from dataclasses import dataclass
from io import StringIO
from typing import Union
from unittest.mock import MagicMock
import pytest

from mocker_builder import MockerBuilder
from testing_heroes import my_heroes
from testing_heroes.my_heroes import (
    Batman, FakeHero, IHero, OtherHero, PeakyBlinder, Robin, MyHeroes
)


def foo():
    print("Something")


class TestMyHeroes(MockerBuilder):

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
        self.add_mock(
            mock_name="mock_test_io",
            target='sys.stdout',
            new_callable=StringIO
        )

        self.add_mock(
            mock_name="mock_my_heroes_class",
            target=MyHeroes
        )

        self.add_mock(
            mock_name="mock_my_heroes_module",
            target=my_heroes.initialize_other_hero,
        )

        self.add_mock(
            mock_name='mock_my_hero',
            target=MyHeroes,
            attribute='_my_hero',
            **{
                'eating_banana.return_value': "Banana Noooo!",
                'just_says.side_effect': ["Nothing to say!"]
            }
        )

        self.add_mock(
            mock_name="mock_my_class",
            target=OtherHero,
            **{
                'return_value.just_says.return_value': "He feels good!"
            }
        )

        self.add_mock(
            mock_name='mock_who_is_my_hero',
            target=Batman,
            **{
                'return_value.eating_banana.return_value': "doesn't like banana",
                'return_value.wearing_pyjama.return_value': "doesn't wear pyjama",
                'return_value.just_call_for.return_value': "Mocker",
                'return_value.just_says.return_value': "I'm gonna mock you babe!",
            }
        )
        # =================================================

    def test_io(self):
        foo()
        assert self.mock_test_io.getvalue() == 'Something\n'

    def test_mock_my_heroes_class(self):
        my_heroes.who_is_the_best_hero()

        assert self.mock_my_heroes_class.called

    def test_mock_my_heroes_module(self):
        # TODO We need to work on this feature yet
        # self.stop_mock(self.mock_my_heroes_module)
        # my_heroes.who_is_the_best_hero()

        # assert not self.mock_my_heroes_module.called

        # self.start_mock(self.mock_my_heroes_module)
        # TODO when restart the mock self.mock_my_heroes_module
        # loses the reference
        # self.mocker_builder_start()
        my_heroes.who_is_the_best_hero()

        assert self.mock_my_heroes_module.called

    def test_my_hero(self):
        assert self.mock_my_hero.eating_banana() == "Banana Noooo!"
        assert self.mock_my_hero.just_says() == "Nothing to say!"

    def test_my_class(self):
        response = my_heroes.asks_what_other_hero_have_to_say_about_been_hero()
        assert response == "He feels good!"

    def test_who_is_my_hero(self):
        my_heroes.who_is_my_hero(Batman())

        testing = MyHeroes()
        testing.my_hero = my_heroes.Batman()
        testing.who_is_my_hero()
