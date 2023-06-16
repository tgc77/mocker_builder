from __future__ import annotations
from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass
from typing import List


class IHeroHobby(ABC):  # Entity
    what_i_do: str = None

    @abstractmethod
    def get_hobby(cls) -> IHeroHobby:
        raise NotImplementedError("Implement it, your lazy!")


@dataclass
class HobbyHero(IHeroHobby):  # Model
    what_i_do: str = None

    def get_hobby(self) -> IHeroHobby:
        return HobbyHero(
            what_i_do=self.what_i_do
        )


class IHero(ABC):  # Repository
    bananas: int
    pyjamas: int
    nickname: str
    my_hobby: HobbyHero

    @classmethod
    async def which_hero_i_am(cls):
        return f"I am {cls.__name__}"

    async def what_i_do_when_nobody_is_looking(self) -> IHeroHobby:
        return self.my_hobby.get_hobby()

    def get_my_hero_hobby(self) -> IHeroHobby:
        return self.my_hobby.get_hobby()

    def set_my_hero_hobby(self, hobby: str):
        self.my_hobby = HobbyHero(hobby)

    @abstractmethod
    def eating_banana(self) -> str:
        pass

    @abstractmethod
    def wearing_pyjama(self) -> str:
        pass

    @abstractmethod
    def just_call_for(self) -> str:
        pass

    @abstractmethod
    def just_says(self) -> str:
        pass


@dataclass
class FakeHero(IHero):
    bananas: int = 2
    pyjamas: int = 2
    nickname: str = 'Bad Fat Hero'
    my_hobby: HobbyHero = None

    def eating_banana(self):
        return f"is eating {self.bananas} banana(s)"

    def wearing_pyjama(self):
        return f"is wearing {self.pyjamas} pyjama(s)"

    def just_call_for(self):
        return f"just calls for {self.nickname}"

    def just_says(self):
        return "I'm fake hero man!"

    def to_dict(self):
        return {
            'bananas': self.bananas,
            'pyjamas': self.pyjamas,
            'nickname': self.nickname
        }


@dataclass
class PeakyBlinder(IHero):
    bananas: int = 3
    pyjamas: int = 2
    nickname: str = "Bart Burp"
    my_hobby: HobbyHero = None

    def eating_banana(self):
        return f"is eating {self.bananas} banana(s)"

    def wearing_pyjama(self):
        return f"is wearing {self.pyjamas} pyjama(s)"

    def just_call_for(self):
        return f"just calls for {self.nickname}"

    def just_says(self):
        return "One more shot of whiskey or I'll shoot you"


@dataclass
class Batman(IHero):
    bananas: int = 5
    pyjamas: int = 1
    nickname: str = "Big Fat Bat"
    my_hobby: HobbyHero = None

    def eating_banana(self):
        return f"is eating {self.bananas} banana(s)"

    def wearing_pyjama(self):
        return f"is wearing {self.pyjamas} pyjama(s)"

    def just_call_for(self):
        return f"just calls for {self.nickname}"

    def just_says(self):
        return "I'm gonna have lunch in the bat cave!"


@dataclass
class Robin(IHero):
    bananas: int = 1
    pyjamas: int = 4
    nickname: str = "Little Bastard"
    my_hobby: HobbyHero = None

    def eating_banana(self):
        return f"is eating {self.bananas} banana(s)"

    def wearing_pyjama(self):
        return f"is wearing {self.pyjamas} pyjama(s)"

    def just_call_for(self):
        return f"just calls for {self.nickname}"

    def just_says(self):
        return "I'm gonna have a pint!"


@dataclass
class OtherHero(IHero):
    bananas: int = 1
    pyjamas: int = 1
    nickname: str = "Bob"
    my_hobby: HobbyHero = None

    def eating_banana(self):
        return f"is eating {self.bananas} banana(s)"

    def wearing_pyjama(self):
        return f"is wearing {self.pyjamas} pyjama(s)"

    def just_call_for(self):
        return f"just calls for {self.nickname}"

    def just_says(self):
        return "Ouieh!"


class MyHeroes:  # HeroesRepository
    _my_hero: IHero = None

    @property
    def my_hero(self) -> IHero:
        return self._my_hero

    @my_hero.setter
    def my_hero(self, hero):
        self._my_hero = hero

    def run_created_runtime_method(self):
        try:
            response = self.runtime_method()
            print(response)
        except Exception as ex:
            print(f"Oops! {repr(ex)}")

    def does(self) -> str:
        hero_hobby = self._my_hero.get_my_hero_hobby()
        return hero_hobby.what_i_do

    def set_what_my_hero_does(self, hobby: str):
        self.my_hero.set_my_hero_hobby(hobby)

    async def what_my_hero_does_when_nobody_is_looking(self):
        return await self._my_hero.what_i_do_when_nobody_is_looking()

    def is_eating_banana(self) -> str:
        return self._my_hero.eating_banana()

    def is_wearing_pyjama(self) -> str:
        return self._my_hero.wearing_pyjama()

    def just_call_for(self) -> str:
        return self._my_hero.just_call_for()

    def just_says(self) -> str:
        return self._my_hero.just_says()

    def who_is_my_hero(self):
        print(f"""
        {self._my_hero.__class__.__name__}, also called by {self._my_hero.nickname}
        is my hero because {self.is_eating_banana()},
        {self.is_wearing_pyjama()}, {self.just_call_for()} and just says:
        {self.just_says()}
        """)


class SomeoneWhoLovesHero():
    _my_hero: IHero = None

    @property
    def my_hero(self):
        return self._my_hero

    @my_hero.setter
    def my_hero(self, hero):
        self._my_hero = hero

    def asks_to_other_hero_about_been_hero(self):
        return self._my_hero.just_says()


def asks_what_other_hero_have_to_say_about_been_hero():
    someone_who_loves_hero = SomeoneWhoLovesHero()
    someone_who_loves_hero.my_hero = OtherHero()
    return someone_who_loves_hero.asks_to_other_hero_about_been_hero()


THE_BEST_HERO: IHero = PeakyBlinder()
OTHER_HERO: IHero = None
UGLY_HERO: str = 'Me'


def who_is_my_hero(_my_hero: IHero = None):
    testing = MyHeroes()
    testing.my_hero = _my_hero if _my_hero else Batman()
    testing.who_is_my_hero()


def who_is_the_best_hero():
    initialize_other_hero()
    who_is_my_hero(THE_BEST_HERO)


def initialize_other_hero():
    global OTHER_HERO
    OTHER_HERO = FakeHero()


class JusticeLeague:

    def __init__(self) -> None:
        self._heroes: List[IHero] = []

    def join_hero(self, hero: IHero):
        self._heroes.append(hero)

    def show_heroes(self):
        if hasattr(self, '_heroes'):
            for hero in self._heroes:
                print(
                    hero.__class__.__name__,
                    hero.just_call_for()
                )
            return
        return "Opss! No heroes over here!"

    def what_heroes_does(self):
        if hasattr(self, '_heroes'):
            for hero in self._heroes:
                print("===========================")
                print(hero.nickname)
                print(hero.eating_banana())
                print(hero.wearing_pyjama())
                print(hero.just_says())
        else:
            return "Eita! Heroes are doing nothing!"

    def how_can_we_call_for_heores(self):
        if hasattr(self, '_heroes'):
            response = []
            for hero in self._heroes:
                response.append((
                    hero.__class__.__name__,
                    hero.just_call_for()
                ))
            return response
        return "Opss! No heroes over here to call for!"

    async def call_heroes(self):
        if hasattr(self, '_heroes'):
            response = []
            for hero in self._heroes:
                response.append((
                    hero.__class__.__name__,
                    "Come on",
                    hero.nickname
                ))
            return response
        return "Uuhmm! Nobody here!"

    async def call_everybody(self):
        await asyncio.sleep(1)
        return await self.call_heroes()

    async def are_heroes_sleeping(self):
        if hasattr(self, '_heroes'):
            for hero in self._heroes:
                yield (
                    f"{hero.__class__.__name__}=>({hero.nickname}): ZZzzzz"
                )
                await asyncio.sleep(.5)
        else:
            await asyncio.sleep(.5)
            yield "=== Heroes are awakened ==="


__all__ = [
    "IHero",
    "FakeHero",
    "PeakyBlinder",
    "Batman",
    "Robin",
    "MyHeroes",
    "JusticeLeague",
    "THE_BEST_HERO",
    "OTHER_HERO",
    "who_is_my_hero",
    "who_is_the_best_hero",
]
