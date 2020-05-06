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


all_chars = (Character.Assassin, Character.Thief, Character.Magician, Character.King,
             Character.Bishop, Character.Merchant, Character.Architect, Character.Warlord)


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


all_colors = (Color.Red, Color.Yellow, Color.Green, Color.Blue) # TODO: add purple


class DistrictInfo:
    def __init__(self, district: District):
        Info = namedtuple('Info', ['name', 'color', 'cost', 'mul'])
        info = {
            District.Watchtower: Info('Watchtower', Color.Red, 1, 3),
            District.Prison: Info('Prison', Color.Red, 2, 3),
            District.Battlefield: Info('Battlefield', Color.Red, 3, 3),
            District.Fortress: Info('Fortress', Color.Red, 4, 2),

            District.Tavern: Info('Tavern', Color.Green, 1, 5),
            District.TradingPost: Info('Trading Post', Color.Green, 2, 3),
            District.Market: Info('Market', Color.Green, 2, 4),
            District.Docks: Info('Docks', Color.Green, 3, 3),
            District.Harbor: Info('Harbor', Color.Green, 4, 3),
            District.TownHall: Info('Town Hall', Color.Green, 5, 2),

            District.Temple: Info('Temple', Color.Blue, 1, 3),
            District.Church: Info('Church', Color.Blue, 2, 3),
            District.Monastery: Info('Monastery', Color.Blue, 3, 3),
            District.Cathedral: Info('Cathedral', Color.Blue, 5, 2),

            District.Manor: Info('Manor', Color.Yellow, 3, 5),
            District.Castle: Info('Castle', Color.Yellow, 4, 4),
            District.Palace: Info('Palace', Color.Yellow, 5, 3),
        }[district]
        self.name = info.name
        self.color = info.color
        self.cost = info.cost
        self.mul = info.mul


class CharacterInfo:
    def __init__(self, char: Character):
        Info = namedtuple('Info', ['name', 'color'])
        info = {
            Character.Assassin: Info('Assassin', None),
            Character.Thief: Info('Thief', None),
            Character.Magician: Info('Magician', None),
            Character.King: Info('King', Color.Yellow),
            Character.Bishop: Info('Bishop', Color.Blue),
            Character.Merchant: Info('Merchant', Color.Green),
            Character.Architect: Info('Architect', None),
            Character.Warlord: Info('Warlord', Color.Red),
        }[char]
        self.name = info.name
        self.color = info.color


def standard_chars():
    return [Character.Assassin, Character.Thief, Character.Magician, Character.King,
            Character.Bishop, Character.Merchant, Character.Architect, Character.Warlord]


def simple_districts():
    cards = [District.TownHall, District.Watchtower, District.Prison, District.TradingPost,
             District.Battlefield, District.Docks, District.Temple, District.Harbor,
             District.Church, District.Palace, District.Monastery, District.Market,
             District.Fortress, District.Castle, District.Cathedral, District.Tavern,
             District.Manor]
    return tuple(chain.from_iterable([district] * DistrictInfo(district).mul for district in cards))


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

    def __repr__(self):
        return 'None' if self._locked else str(self._payload)


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
        return tuple(self._cards)

    def take_random(self):
        return self._cards.pop(random.randint(0, len(self._cards)-1))

    def take(self, card):
        self._cards.remove(card)
        return card

    def __len__(self):
        return len(self._cards)

    def __iter__(self):
        return iter(self._cards)

    def __getitem__(self, item):
        return self._cards[item]
