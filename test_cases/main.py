from io import StringIO
from unittest.mock import PropertyMock
import pytest

from mocker_builder import MockerBuilder
from test_cases import my_heroes
from test_cases.my_heroes import (
    Batman,
    HobbyHero,
    IHero,
    JusticeLeague,
    OtherHero,
    PeakyBlinder,
    MyHeroes,
    Robin
)


def print_io_test():
    print("Ouieh!!!")


class Foo(IHero):
    nickname: str = "Bob"

    def eating_banana(self) -> str:
        return "have no banana"

    def wearing_pyjama(self) -> str:
        return "have no pyjama"

    def just_call_for(self) -> str:
        return "Bob Foo"

    def just_says(self) -> str:
        return "foo foo"


class TestMyHeroes(MockerBuilder):
    """Main Test Class to implement MockerBuilder features to make your tests"""

    @MockerBuilder.initializer
    def mocker_builder_setup(self):
        # ================== Setting fixtures ===================
        self.my_hero = self.add_fixture(
            content=lambda: (yield PeakyBlinder(
                bananas=12,
                pyjamas=7,
                nickname="Thomas Shelby"
            ))
        )
        # =================== Setting mocks ======================
        self.what_i_do_when_nobody_is_looking = self.patch(
            PeakyBlinder,
            'what_i_do_when_nobody_is_looking',
            return_value=HobbyHero("I just drink wisky")
        )
        self.get_my_hero_hobby = self.patch(
            Robin,
            'get_my_hero_hobby',
            return_value=HobbyHero("I just watch TV")
        )
        self.mock_my_heroes_module = self.patch(
            target=my_heroes.initialize_other_hero
        )
        self.mock_my_hero_attribue = self.patch(
            target=MyHeroes,
            attribute='_my_hero',
            mock_configure={
                'eating_banana.return_value': "Banana Noooo!",
                'just_says.side_effect': ["Nothing to say!"]
            }
        )
        self.mock_other_hero = self.patch(
            target=OtherHero,
            mock_configure={
                'return_value.just_says.return_value': "He feels good!"
            }
        )
        self.my_hero_batman = self.patch(
            # XXX or target='main.Batman' to mock the Batman class imported from here.
            target=Batman,
            mock_configure={
                'return_value.nickname': 'Bat Mock',
                'return_value.eating_banana.return_value': "doesn't like banana",
                'return_value.wearing_pyjama.return_value': "doesn't wear pyjama",
                'return_value.just_call_for.return_value': "just calls for Mocker",
                'return_value.just_says.return_value': "I'm gonna mock you babe!",
            }
        )
        self.mock_justice_league__init__ = self.patch(
            target=JusticeLeague.__init__
        )
        # ========================================================

    def test_io(self):
        self.test_print_io = self.patch(
            target='sys.stdout',
            new_callable=StringIO
            # spec=StringIO
        )
        print_io_test()
        # assert self.test_print_io.mock.called
        assert self.test_print_io.mock.getvalue() == 'Ouieh!!!\n'

    def test_another_print_io(self):
        self.test_print_io = self.patch(
            target='sys.stdout',
            new_callable=StringIO
        )
        patched_print_io_test = self.patch(
            target=print_io_test,
            side_effect=[print("Ooouuiieeh!!")]
        )
        print_io_test()
        assert not self.test_print_io.mock.getvalue() == 'Ouieh!!!\n'
        assert self.test_print_io.mock.getvalue() == 'Ooouuiieeh!!\n'
        patched_print_io_test.mock.assert_called()

    def test_robin_becomes_batman(self):
        self.robin_becomes_batman = self.patch(
            Robin,
            new=Batman
        )
        robin = Robin()
        assert robin.nickname == "Little Bastard"

        robin.nickname = "Bat Robinson"
        assert not self.robin_becomes_batman.mock.nickname == "Bat Robinson"
        assert self.robin_becomes_batman.mock.nickname == "Big Fat Bat"

        # self.robin_becomes_batman.stop()
        assert not robin.nickname == "Little Bastard"
        assert robin.nickname == "Bat Robinson"

    @pytest.mark.asyncio
    async def test_what_i_do_when_nobody_is_looking(self):
        # ----------------------- PeakyBlinder ----------------------
        him = MyHeroes()
        him.my_hero = PeakyBlinder(
            my_hobby=HobbyHero(
                what_i_do="Shot someone"
            )
        )
        peaky_blinder = await him.what_my_hero_does_when_nobody_is_looking()

        assert self.what_i_do_when_nobody_is_looking.mock.called
        assert not peaky_blinder.what_i_do == "Shot someone"
        assert peaky_blinder.what_i_do == "I just drink wisky"
        assert him.does() == "Shot someone"
        assert not him.does() == "I just drink wisky"

        self.what_i_do_when_nobody_is_looking.set_result(
            return_value=HobbyHero("Just relax!")
        )
        peaky_blinder = await him.what_my_hero_does_when_nobody_is_looking()

        assert not peaky_blinder.what_i_do == "I just drink wisky"
        assert peaky_blinder.what_i_do == "Just relax!"
        assert him.does() == "Shot someone"
        assert not him.does() == "just relax!"

        # ----------------------- Robin ----------------------
        robs = MyHeroes()
        robs.my_hero = Robin(
            my_hobby=HobbyHero(
                what_i_do="I catch bad guys"
            )
        )
        robin = await robs.what_my_hero_does_when_nobody_is_looking()

        assert not self.get_my_hero_hobby.mock.called
        assert not robin.what_i_do == "I just watch TV"
        assert robin.what_i_do == "I catch bad guys"

        # calling does() method calls mocked Robin.get_my_hero_hobby method so get the mocked value
        assert not robs.does() == "I catch bad guys"
        assert robs.does() == "I just watch TV"
        assert self.get_my_hero_hobby.mock.called
        assert self.get_my_hero_hobby.mock.call_count == 2

        # ================================================================================
        # -------------------- Robin -> Batman --------------------
        self.robin_becomes_batman = self.patch(
            Robin,
            new=Batman
        )
        self.get_my_hero_hobby.stop()

        # Here now we will actually mock Batman.get_my_hero_hobby calling
        self.get_my_hero_hobby = self.patch(
            Robin,
            'get_my_hero_hobby',
            return_value=HobbyHero("I just watch TV")
        )
        robs = MyHeroes()
        robs.my_hero = Robin(
            my_hobby=HobbyHero(
                what_i_do="I catch bad guys"
            )
        )
        robin = await robs.what_my_hero_does_when_nobody_is_looking()

        assert not self.get_my_hero_hobby.mock.called
        assert not robin.what_i_do == "I just watch TV"
        assert robin.what_i_do == "I catch bad guys"

        # calling does() method calls mocked Batman.get_my_hero_hobby method so get the mocked value
        assert robs.does() == "I catch bad guys"
        assert not robs.does() == "I just watch TV"
        assert not self.get_my_hero_hobby.mock.called
        assert self.get_my_hero_hobby.mock.call_count == 0

        # ----------------------------------------------------------------
        # remember we mocked robin as batman => self.robin_becomes_batman
        # ----------------------------------------------------------------
        bats = MyHeroes()
        bats.my_hero = Batman(
            my_hobby=HobbyHero(
                what_i_do="I catch bad guys"
            )
        )
        batman = await robs.what_my_hero_does_when_nobody_is_looking()

        assert not self.get_my_hero_hobby.mock.called
        assert not batman.what_i_do == "I just watch TV"
        assert batman.what_i_do == "I catch bad guys"
        assert bats.does() == "I just watch TV"
        assert not bats.does() == "I catch bad guys"
        assert self.get_my_hero_hobby.mock.called
        assert self.get_my_hero_hobby.mock.call_count == 2

    @pytest.mark.asyncio
    async def test_heroes_sleeping(self):
        justce_league = JusticeLeague()
        assert self.mock_justice_league__init__().called

        async def hero_names():
            yield Batman().nickname
            yield Robin().nickname
        _hero_names = hero_names()

        async for result in justce_league.are_heroes_sleeping():
            assert result == "=== Heroes are awakened ==="

        self.mock_justice_league__init__.stop()
        justce_league = JusticeLeague()

        async for result in justce_league.are_heroes_sleeping():
            _hero_name = await _hero_names.__anext__()
            print(result, _hero_name)
            assert result == f"MagicMock=>({_hero_name}): ZZzzzz"

    @pytest.mark.asyncio
    async def test_call_heroes(self):
        # Remember that JusticeLeague.__init__ still mocked, so calling JusticeLeague() doesn't
        # initialize JusticeLeague._heroes attribute.

        justce_league = JusticeLeague()
        assert await justce_league.call_everybody() == "Uuhmm! Nobody here!"

        with pytest.raises(AttributeError) as ex:
            justce_league.join_hero(Batman())
        assert "'JusticeLeague' object has no attribute '_heroes'" == str(ex.value)

        # We just stop mocking JusticeLeague.__init__ to test a different behavior below
        self.mock_justice_league__init__.stop()
        del justce_league

        with self.patch(
            JusticeLeague,
            '_heroes',
            create=True,
            return_value=PropertyMock(spec=list, return_value=[])
        ):

            justce_league = JusticeLeague()
            justce_league.join_hero(Batman())
            # my_heroes.Batman() still mocked
            justce_league.join_hero(my_heroes.Batman())

            assert await justce_league.call_everybody() == [
                ('Batman', 'Come on', 'Big Fat Bat'),
                ('MagicMock', 'Come on', 'Bat Mock')
            ]

    def test_mock_my_heroes_class(self):
        mock_my_heroes_class = self.patch(
            target=MyHeroes
        )
        my_heroes.who_is_the_best_hero()
        assert mock_my_heroes_class().called

    def test_mock_my_heroes_module(self):
        self.mock_my_heroes_module.stop()
        my_heroes.who_is_the_best_hero()
        assert not self.mock_my_heroes_module().called

        self.mock_my_heroes_module.start()
        my_heroes.who_is_the_best_hero()
        assert self.mock_my_heroes_module().called

    def test_mock_my_hero_attribute(self):
        assert self.mock_my_hero_attribue().eating_banana() == "Banana Noooo!"
        assert self.mock_my_hero_attribue.mock.just_says() == "Nothing to say!"

    def test_mock_my_class(self):
        response = my_heroes.asks_what_other_hero_have_to_say_about_been_hero()
        assert response == "He feels good!"

    def test_my_hero_batman(self):
        my_heroes.who_is_my_hero(Batman())

        testing = MyHeroes()
        testing.my_hero = my_heroes.Batman()
        testing.who_is_my_hero()

        assert self.my_hero_batman.mock.return_value.nickname == 'Bat Mock'
        assert testing.my_hero.nickname == 'Bat Mock'

    def test_mock_justice_league__init__(self):
        justce_league = JusticeLeague()
        assert justce_league.show_heroes() == "Opss! No heroes over here!"
        assert justce_league.what_heroes_does() == "Eita! Heroes are doing nothing!"

        self.mock_justice_league__init__.stop()

        justce_league = JusticeLeague()
        # my_heroes.Batman() is mocked
        justce_league.join_hero(my_heroes.Batman())
        justce_league.join_hero(Robin())

        mock_test_io = self.patch(
            target='sys.stdout',
            new_callable=StringIO
        )
        justce_league.show_heroes()
        expected = """MagicMock just calls for Mocker
Robin just calls for Little Bastard\n"""
        assert mock_test_io().getvalue() == expected

        justce_league.what_heroes_does()
        expected += """===========================
Bat Mock
doesn't like banana
doesn't wear pyjama
I'm gonna mock you babe!
===========================
Little Bastard
is eating 1 banana(s)
is wearing 4 pyjama(s)
I'm gonna have a pint!\n"""
        assert mock_test_io().getvalue() == expected

        mock_test_io.stop()
        self.mock_justice_league__init__.start()

        justce_league = JusticeLeague()
        assert justce_league.show_heroes() == "Opss! No heroes over here!"
        assert justce_league.what_heroes_does() == "Eita! Heroes are doing nothing!"

    def test_mock_ugly_hero(self):

        assert my_heroes.UGLY_HERO == 'Me'

        mock_ugly_hero = self.patch(
            target=my_heroes,
            attribute='UGLY_HERO',
            mock_configure={
                'third': 'You',
                'who_is_the_most_ugly.return_value': 'Me again',
            },
            first='Batman',
            second='Robin',
            call_me_a_hero=lambda: PeakyBlinder().nickname
        )
        mock_ugly_hero.configure_mock(
            fourth='Me',
            **{
                'who_is_my_hero.return_value': Batman().nickname,
                'who_is_the_most_beautiful.side_effect': ValueError("There isn't any beautiful hero")
            }
        )

        assert mock_ugly_hero().first == 'Batman'
        assert mock_ugly_hero().second == 'Robin'
        assert mock_ugly_hero().third == 'You'
        assert mock_ugly_hero().fourth == 'Me'
        assert mock_ugly_hero().who_is_the_most_ugly() == 'Me again'
        assert mock_ugly_hero().call_me_a_hero() == "Bart Burp"
        assert mock_ugly_hero().who_is_my_hero() == "Big Fat Bat"

        with pytest.raises(ValueError) as ex:
            mock_ugly_hero().who_is_the_most_beautiful()
        assert "There isn't any beautiful hero" == str(ex.value)

    def test_how_can_we_call_for_heores(self):
        self.mock_justice_league__init__.stop()
        self.my_hero_batman.stop()

        justce_league = JusticeLeague()
        # my_heroes.Batman() is mocked but was stopped
        justce_league.join_hero(my_heroes.Batman())
        justce_league.join_hero(Robin())
        assert justce_league.how_can_we_call_for_heores() == [
            ("Batman", "just calls for Big Fat Bat"),
            ("Robin", "just calls for Little Bastard")
        ]
        self.mock_justice_league__init__.start()
        justce_league = JusticeLeague()
        assert self.mock_justice_league__init__().called
        assert justce_league.how_can_we_call_for_heores() == "Opss! No heroes over here to call for!"

        self.my_hero_batman.start()
        self.mock_justice_league__init__.stop()

        justce_league = JusticeLeague()
        # my_heroes.Batman() is mocked and was started again
        justce_league.join_hero(my_heroes.Batman())
        justce_league.join_hero(Robin())
        assert justce_league.how_can_we_call_for_heores() == [
            ("MagicMock", "just calls for Mocker"),
            ("Robin", "just calls for Little Bastard")
        ]
        assert self.my_hero_batman.mock.called

    def test_my_hero_robin(self):
        my_hero_robin = self.patch(
            target=Robin(),  # XXX we can mock from object instance! Ouieh!
            return_value=PropertyMock(
                nickname='Bastard Mock',
                eating_banana=lambda: "eat a lot of bananas",
                wearing_pyjama=lambda: "likes to be naked",
                just_call_for=lambda: "Little Mocker",
                just_says=lambda: "Mock me baby!"
            )
        )

        my_heroes.who_is_my_hero(Robin())
        testing = MyHeroes()
        testing.my_hero = my_heroes.Robin()
        testing.who_is_my_hero()

        assert my_hero_robin.mock.called
        assert my_hero_robin.mock.return_value.nickname == 'Bastard Mock'
        assert my_hero_robin.mock.return_value.eating_banana() == "eat a lot of bananas"
        assert my_hero_robin.mock.return_value.wearing_pyjama() == "likes to be naked"
        assert my_hero_robin.mock.return_value.just_call_for() == "Little Mocker"
        assert my_hero_robin.mock.return_value.just_says() == "Mock me baby!"

    def test_set_result_return_value(self):
        my_hero_robin = self.patch(
            target=Robin,
            return_value=Foo()
        )

        print("--------------------------------------------------------------------------")
        print("Who is my hero:")
        print("--------------------------------------------------------------------------")
        my_heroes.who_is_my_hero(Robin())

        testing = MyHeroes()
        testing.my_hero = my_heroes.Robin()
        print("--------------------------------------------------------------------------")
        print("Who is my mocked hero with return_value = Foo():")
        print("--------------------------------------------------------------------------")
        testing.who_is_my_hero()

        assert my_hero_robin.mock.called
        assert isinstance(my_hero_robin.mock.return_value, Foo)

        print("--------------------------------------------------------------------------")
        print("Setting mock result return_value=PeakyBlinder()")
        print("--------------------------------------------------------------------------")
        my_hero_robin.set_result(
            return_value=PeakyBlinder()
        )
        assert not isinstance(my_hero_robin.mock.return_value, Foo)
        assert isinstance(my_hero_robin.mock.return_value, PeakyBlinder)

        testing = MyHeroes()
        testing.my_hero = my_heroes.Robin()
        print("--------------------------------------------------------------------------")
        print("Who is my mocked hero with return_value = PeakyBlinder():")
        print("--------------------------------------------------------------------------")
        testing.who_is_my_hero()

    def test_set_result_side_effect(self):
        my_hero_robin = self.patch(
            target=PeakyBlinder,
            side_effect=lambda: Foo()
        )

        print("--------------------------------------------------------------------------")
        print("Who is my hero:")
        print("--------------------------------------------------------------------------")
        my_heroes.who_is_my_hero(PeakyBlinder())

        testing = MyHeroes()
        testing.my_hero = my_heroes.PeakyBlinder()
        print("--------------------------------------------------------------------------")
        print("Who is my mocked hero with side_effect = Foo():")
        print("--------------------------------------------------------------------------")
        testing.who_is_my_hero()

        assert my_hero_robin.mock.called
        assert isinstance(testing.my_hero, Foo)

        print("--------------------------------------------------------------------------")
        print("""Setting mock result side_effect=[
    OtherHero(),
    TypeError('Ops! No hero like that!')
]""")
        print("--------------------------------------------------------------------------")
        my_hero_robin.set_result(
            side_effect=[OtherHero(), TypeError("Ops! No hero like that!")]
        )
        testing.my_hero = my_heroes.PeakyBlinder()

        assert not isinstance(testing.my_hero, Foo)
        assert isinstance(testing.my_hero, OtherHero)

        print("--------------------------------------------------------------------------")
        print("Who is my mocked hero with side_effect = OtherHero():")
        print("--------------------------------------------------------------------------")
        testing.who_is_my_hero()

        print("--------------------------------------------------------------------------")
        print("Testing side_effect = TypeError('Ops! No hero like that!')")
        print("--------------------------------------------------------------------------")
        with pytest.raises(TypeError) as ex:
            testing.my_hero = my_heroes.PeakyBlinder()
            testing.who_is_my_hero()
        assert "Ops! No hero like that!" == str(ex.value)

    def test_create_my_heroes_method_runtime(self):
        runtime_method = self.patch(
            target=MyHeroes,
            method='runtime_method',
            create=True,
            # return_value="Ouieh! I'm runtime method running...", # Also works
            # mock_configure={
            #     'return_value': "Ouieh! I'm runtime created method running..." # Also works
            # },
        )
        runtime_method.configure_mock(
            return_value="Ouieh! I'm runtime created method running..."
        )
        _my_heroes = MyHeroes()
        _my_heroes.run_created_runtime_method()
        assert runtime_method.mock.called
