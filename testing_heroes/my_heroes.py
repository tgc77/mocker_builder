from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass


class IHero(ABC):
    bananas: int
    pyjamas: int
    nickname: str

    @abstractmethod
    def eating_banana(self):
        pass

    @abstractmethod
    def wearing_pyjama(self):
        pass

    @abstractmethod
    def just_call_for(self):
        pass

    @abstractmethod
    def just_says(self):
        pass


@dataclass
class FakeHero(IHero):
    bananas: int = 2
    pyjamas: int = 2
    nickname: str = 'Bad Fat Hero'

    def eating_banana(self):
        return f"is eating {self.bananas} banana(s)!"

    def wearing_pyjama(self):
        return f"is wearing {self.pyjamas} pyjama(s)!"

    def just_call_for(self):
        return f"just calls for {self.nickname}"

    def just_says(self):
        return "just says: I'm fake hero man!"

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
    nickname: str = "Tomas Shelby"

    def eating_banana(self):
        return f"is eating {self.bananas} banana(s)!"

    def wearing_pyjama(self):
        return f"is wearing {self.pyjamas} pyjama(s)!"

    def just_call_for(self):
        return f"just calls for {self.nickname}"

    def just_says(self):
        return "just says: One more shot of whiskey or I'll shoot you"


@dataclass
class Batman(IHero):
    bananas: int = 5
    pyjamas: int = 1
    nickname: str = "Big Fat Bat"

    def eating_banana(self):
        return f"is eating {self.bananas} banana(s)!"

    def wearing_pyjama(self):
        return f"is wearing {self.pyjamas} pyjama(s)!"

    def just_call_for(self):
        return f"just calls for {self.nickname}"

    def just_says(self):
        return "just says: I'm gonna have lunch in the bat cave!"


@dataclass
class Robin(IHero):
    bananas: int = 1
    pyjamas: int = 4
    nickname: str = "Little Bastard"

    def eating_banana(self):
        return f"is eating {self.bananas} banana(s)!"

    def wearing_pyjama(self):
        return f"is wearing {self.pyjamas} pyjama(s)!"

    def just_call_for(self):
        return f"just calls for {self.nickname}"

    def just_says(self):
        return "just says: I'm gonna have a pint!"

    def who_is_my_hero(self):
        print(f"My hero is {self.__class__.__name__}")


class TestingHeroes:
    _my_hero: IHero = Batman()

    def __call__(self, my_hero: IHero) -> TestingHeroes:
        self._my_hero = my_hero
        self.hero_name = self._my_hero.__class__.__name__
        return self

    def is_eating_banana(self) -> str:
        return self._my_hero.eating_banana() if self._my_hero.bananas > 0 else \
            "don't have any banana"

    def is_wearing_pyjama(self) -> str:
        return self._my_hero.wearing_pyjama() if self._my_hero.pyjamas > 0 else \
            "is not wearing pyjama"

    def just_call_for(self) -> str:
        return self._my_hero.just_call_for()

    def just_says(self) -> str:
        return self._my_hero.just_says()

    def who_is_my_hero(self):
        print(f"""
        {self.hero_name} is my hero because {self.is_eating_banana()}, 
        {self.is_wearing_pyjama()}, {self.just_call_for()} and 
        {self.just_says()}
        """)


THE_BEST_HERO: IHero = PeakyBlinder()
OTHER_HERO: IHero = None


def who_is_my_hero(_my_hero: IHero = None):
    testing = TestingHeroes()(_my_hero)

    testing.who_is_my_hero()


def who_is_the_best_hero():
    who_is_my_hero(THE_BEST_HERO)


def initialize_other_hero():
    global OTHER_HERO
    OTHER_HERO = FakeHero()


initialize_other_hero()

__all__ = [
    "IHero",
    "FakeHero",
    "PeakyBlinder",
    "Batman",
    "Robin",
    "TestingHeroes",
    "THE_BEST_HERO",
    "OTHER_HERO",
    "who_is_my_hero",
    "who_is_the_best_hero",
]
