# Mocker Builder
Testing tools for mocking and patching based on pytest_mock mocker features.

### Installation
```
pip install mocker-builder
```

### Initializer
To start using mucker-builder features just create your Test class, inherit from MockerBuilder class,
implement the required abstract method mocker_builder_setup decorating it with the @MockerBuilder.initializer
decorator and start building your mocks and fixtures just like that:

```Python
from io import StringIO

from mocker_builder import MockerBuilder
from testing_heroes import my_heroes
from testing_heroes.my_heroes import (
    Batman, JusticeLeague, OtherHero, PeakyBlinder, MyHeroes
)


def print_io_test():
    print("Ouieh!!!")


class TestMyHeroes(MockerBuilder):

    @MockerBuilder.initializer
    def mocker_builder_setup(self):
        print("######################### initializer #######################")
        # ================== Setting fixtures ===================
        # TODO We will work on this feature to implement a real fixture
        self.my_hero = self.add_fixture(
            content=PeakyBlinder(
                bananas=12,
                pyjamas=7,
                nickname="Bellboy"
            )
        )
        # =================== Setting mocks ======================
        self.mock_my_heroes_class = self.add_mock(
            target=MyHeroes
        )

        self.mock_my_heroes_module = self.add_mock(
            target=my_heroes.initialize_other_hero
        )
        self.mock_my_hero = self.add_mock(
            target=MyHeroes,
            attribute='_my_hero',
            configure_mock={
                'eating_banana.return_value': "Banana Noooo!",
                'just_says.side_effect': ["Nothing to say!"]
            }
        )
        self.mock_my_class = self.add_mock(
            target=OtherHero,
            configure_mock={
                'return_value.just_says.return_value': "He feels good!"
            }
        )
        self.mock_who_is_my_hero = self.add_mock(
            target=Batman,
            configure_mock={
                'return_value.eating_banana.return_value': "doesn't like banana",
                'return_value.wearing_pyjama.return_value': "doesn't wear pyjama",
                'return_value.just_call_for.return_value': "Just calls for Mocker",
                'return_value.just_says.return_value': "I'm gonna mock you babe!",
            }
        )
        self.mock_justice_league = self.add_mock(
            target=JusticeLeague.__init__
        )
        # =================================================

    def test_mock_my_heroes_class(self):
        my_heroes.who_is_the_best_hero()

        assert self.mock_my_heroes_class().called

    def test_mock_my_heroes_module(self):
        self.mock_my_heroes_module.stop()
        my_heroes.who_is_the_best_hero()
        assert not self.mock_my_heroes_module().called

        self.mock_my_heroes_module.start()
        my_heroes.who_is_the_best_hero()
        assert self.mock_my_heroes_module().called

    def test_my_hero(self):
        assert self.mock_my_hero().eating_banana() == "Banana Noooo!"
        assert self.mock_my_hero().just_says() == "Nothing to say!"

    def test_my_class(self):
        response = my_heroes.asks_what_other_hero_have_to_say_about_been_hero()
        assert response == "He feels good!"

    def test_who_is_my_hero(self):
        my_heroes.who_is_my_hero(Batman())

        testing = MyHeroes()
        testing.my_hero = my_heroes.Batman()
        testing.who_is_my_hero()

    def test_justice_league_call_heroes(self):
        justce_league = JusticeLeague()

        assert justce_league.show_heroes() == "Opss! No heroes over here!"
        assert justce_league.what_heroes_does() == "Eita! Heroes are doing nothing!"

        self.mock_justice_league.stop()

        justce_league = JusticeLeague()
        justce_league.show_heroes()
        justce_league.what_heroes_does()

        self.mock_justice_league.start()

    def test_my_hero_fixture(self):
        assert self.my_hero.bananas == 12
```

You also can add mocks from your test_... methods, but you must declare the mocker_builder_setup method 
and decorate it with the @MockerBuilder.initializer decorator to be able to use MockerBuilder features.

```Python
...
class TestMyHeroes(MockerBuilder):

    @MockerBuilder.initializer
    def mocker_builder_setup(self):
        pass
...
def test_io(self):
    self.mock_test_io = self.add_mock(
        target='sys.stdout',
        new_callable=StringIO
    )
    print_io_test()
    assert self.mock_test_io().getvalue() == 'Ouieh!!!\n'
```