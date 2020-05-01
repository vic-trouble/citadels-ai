from collections import namedtuple
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


all_chars = frozenset([Character.Assassin, Character.Thief, Character.Magician, Character.King,
                       Character.Bishop, Character.Merchant, Character.Architect, Character.Warlord])


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


class DistrictInfo:
    def __init__(self, district: District):
        Info = namedtuple('Info', ['color', 'cost', 'mul'])
        info = {
            District.Watchtower: Info(Color.Red, 1, 3),
            District.Prison: Info(Color.Red, 2, 3),
            District.Battlefield: Info(Color.Red, 3, 3),
            District.Fortress: Info(Color.Red, 4, 2),

            District.Tavern: Info(Color.Green, 1, 5),
            District.TradingPost: Info(Color.Green, 2, 3),
            District.Market: Info(Color.Green, 2, 4),
            District.Docks: Info(Color.Green, 3, 3),
            District.Harbor: Info(Color.Green, 4, 3),
            District.TownHall: Info(Color.Green, 5, 2),

            District.Temple: Info(Color.Blue, 1, 3),
            District.Church: Info(Color.Blue, 2, 3),
            District.Monastery: Info(Color.Blue, 3, 3),
            District.Cathedral: Info(Color.Blue, 5, 2),

            District.Manor: Info(Color.Yellow, 3, 5),
            District.Castle: Info(Color.Yellow, 4, 4),
            District.Palace: Info(Color.Yellow, 5, 3),
        }[district]
        self.color = info.color
        self.cost = info.cost
        self.mul = info.mul


class CharacterInfo:
    def __init__(self, char: Character):
        Info = namedtuple('Info', ['color'])
        info = {
            Character.King: Info(Color.Yellow),
            Character.Merchant: Info(Color.Green),
            Character.Bishop: Info(Color.Blue),
            Character.Warlord: Info(Color.Red),
        }.get(char, None)
        self.color = info.color if info else None


def standard_chars():
    return [Character.Assassin, Character.Thief, Character.Magician, Character.King,
            Character.Bishop, Character.Merchant, Character.Architect, Character.Warlord]


def simple_districts():
    cards = [District.TownHall, District.Watchtower, District.Prison, District.TradingPost,
             District.Battlefield, District.Docks, District.Temple, District.Harbor,
             District.Church, District.Palace, District.Monastery, District.Market,
             District.Fortress, District.Castle, District.Cathedral, District.Tavern,
             District.Manor]
    return list(chain.from_iterable([district] * DistrictInfo(district).mul for district in cards))


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

    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        if self._locked != other._locked:
            return False
        return self._payload == other._payload if not self._locked else True


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
