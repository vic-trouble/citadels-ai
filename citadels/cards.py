from enum import Enum, IntEnum, auto
from itertools import chain
import random


class Character(IntEnum):
    Assassin = auto()
    Thief = auto()
    Magician = auto()
    King = auto()
    Bishop = auto()
    Merchant = auto()
    Architect = auto()
    Warlord = auto()


class District(Enum):
    TownHall = auto()
    University = auto()
    DragonGate = auto()
    Watchtower = auto()
    Armory = auto()
    Keep = auto()
    HauntedCity = auto()
    MagicSchool = auto()
    Prison = auto()
    BallRoom = auto()
    TradingPost = auto()
    GreatWall = auto()
    Battlefield = auto()
    BellTower = auto()
    Docks = auto()
    Graveyard = auto()
    Temple = auto()
    Factory = auto()
    Harbor = auto()
    Laboratory = auto()
    Church = auto()
    Hospital = auto()
    Palace = auto()
    Smithy = auto()
    Monastery = auto()
    Treasury = auto()
    Market = auto()
    Library = auto()
    Fortress = auto()
    Lighthouse = auto()
    Castle = auto()
    Observatory = auto()
    Cathedral = auto()
    MapRoom = auto()
    Tavern = auto()
    Park = auto()
    Museum = auto()
    PoorHouse = auto()
    Manor = auto()
    WishingWell = auto()
    ThroneRoom = auto()
    Quarry = auto()


class Color(Enum):
    Red = auto()
    Yellow = auto()
    Green = auto()
    Blue = auto()
    Purple = auto()


def standard_chars():
    return [Character.Assassin, Character.Thief, Character.Magician, Character.King,
            Character.Bishop, Character.Merchant, Character.Architect, Character.Warlord]


def simple_districts():
    cards = {District.TownHall: 2,
             District.Watchtower: 3,
             District.Prison: 3,
             District.TradingPost: 3,
             District.Battlefield: 3,
             District.Docks: 3,
             District.Temple: 3,
             District.Harbor: 3,
             District.Church: 3,
             District.Palace: 3,
             District.Monastery: 3,
             District.Market: 4,
             District.Fortress: 2,
             District.Castle: 4,
             District.Cathedral: 2,
             District.Tavern: 5,
             District.Manor: 5}
    return list(chain.from_iterable([district] * mul for district, mul in cards.items()))


class Card:
    def __init__(self, payload):
        self._payload = payload
        self._locked = False

    @property
    def facedown(self):
        self._locked = True
        return self

    def __getattr__(self, item):
        if not hasattr(self._payload, item):
            raise AttributeError(f'unknown attr {item}')
        return None if self._locked else getattr(self._payload, item)

    def __bool__(self):
        return not self._locked


class Deck:
    def __init__(self, cards):
        self._cards = list(cards)

    def shuffle(self):
        random.shuffle(self._cards)

    @property
    def empty(self):
        return bool(self._cards)

    def take_from_top(self):
        return self._cards.pop(0)

    def put_on_bottom(self, card):
        self._cards.append(card)

    @property
    def cards(self):
        return list(self._cards)

    def take_random(self):
        return self._cards.pop(random.randint(0, len(self._cards)-1))

    def take(self, card):
        self._cards.remove(card)
        return card

    def __len__(self):
        return len(self._cards)

    def __iter__(self):
        return iter(self._cards)
