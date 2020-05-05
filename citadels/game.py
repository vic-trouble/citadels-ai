from collections import defaultdict
from copy import deepcopy

from citadels.cards import Character, Deck, District
from citadels.event import EventSource


class GameError(RuntimeError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Bank:
    def __init__(self):
        self._accounts = defaultdict(lambda: BankAccount(self))

    def account(self, key):
        """ Player's account """
        return self._accounts[key]


class BankAccount:
    def __init__(self, bank: Bank):
        self._bank = bank
        self._balance = 0

    @property
    def balance(self):
        """ Account balance, cannot be negative """
        return self._balance

    def withdraw(self, amount):
        """ Withdraw money from the account """
        assert amount > 0
        if amount > self._balance:
            raise GameError('not enough gold on the account (requested {amount} from {balance})'.format(amount=amount, balance=self._balance))
        self._balance -= amount
        return amount

    def cash_in(self, amount):
        """ Put money into the account """
        assert amount > 0
        self._balance += amount
        return amount


class PlayerListener:
    def cashed_in(self, player, amount: int):
        pass

    def withdrawn(self, player, amount: int):
        pass

    def picked_char(self, player, char: Character):
        pass

    def taken_card(self, player, district: District):
        pass

    def district_built(self, player, district: District):
        pass

    def district_lost(self, player, district: District):
        pass

    def swapped_hands(self, player, other_player):
        pass

    def replaced_hand(self, player, amount: int):
        pass


class Player(EventSource):
    def __init__(self, player_id, game, char=None, hand=None, city=None):
        super().__init__()
        self.name = ''
        self._id = player_id
        self._game = game
        self._char = char
        self._hand = list(hand) if hand else []
        self._city = list(city) if city else []

    @property
    def player_id(self):
        """ Unique ID for a give game """
        return self._id

    @property
    def _bank_account(self):
        return self._game.bank.account(self._id)

    @property
    def gold(self):
        """ Amount of player's gold """
        return self._bank_account.balance

    def cash_in(self, amount):
        """ Give some gold """
        amount = self._bank_account.cash_in(amount)
        self.fire_event('cashed_in', self, amount)
        return amount

    def withdraw(self, amount):
        """ Remove some gold """
        amount = self._bank_account.withdraw(amount)
        self.fire_event('withdrawn', self, amount)
        return amount

    def __repr__(self):
        return 'Player("{}")'.format(self.name)

    @property
    def char(self):
        return self._char

    @char.setter
    def char(self, value):
        self._char = value
        self.fire_event('picked_char', self, self._char)

    @property
    def city(self):
        return tuple(self._city)

    @property
    def hand(self):
        return tuple(self._hand)

    def take_card(self, district: District):
        self._hand.append(district)
        self.fire_event('taken_card', self, district)

    def remove_card(self, district: District):
        self._hand.remove(district)
        self.fire_event('removed_card', self, district)

    def build_district(self, district: District):
        self._city.append(district)
        self.fire_event('district_built', self, district)

    def destroy_district(self, district: District):
        self._city.remove(district)
        self.fire_event('district_lost', self, district)


class Turn:
    def __init__(self, game):
        self._game = game
        self._unused_chars = []
        self._killed_char = None
        self._robbed_char = None

    def drop_char(self, char: Character):
        """ Remove character from playable set """
        self._unused_chars.append(char)

    @property
    def unused_chars(self):
        return tuple(self._unused_chars)

    @property
    def killed_char(self):
        return self._killed_char

    @killed_char.setter
    def killed_char(self, char):
        assert char
        self._killed_char = char
        self._game.fire_event('murder_announced', char)

    @property
    def robbed_char(self):
        return self._robbed_char

    @robbed_char.setter
    def robbed_char(self, char):
        assert char
        self._robbed_char = char
        self._game.fire_event('theft_announced', char)


class PlayersProxy:
    def __init__(self, players, crowned_player):
        self._players = players
        self._crowned_player = crowned_player

    def __iter__(self):
        return iter(self._players)

    def __len__(self):
        return len(self._players)

    def __getitem__(self, item):
        return self._players[item]

    def order_by_char_selection(self):
        """ Players in order of character selection """
        index = self.crowned_index
        if index == -1:
            return tuple(self._players)
        else:
            return tuple(self._players[index:] + self._players[:index])

    def order_by_take_turn(self):
        """ Players in order of making their turn """
        return tuple(sorted(self._players, key=lambda p: p.char))

    def find_by_name(self, name):
        """ Return first player with given name or None """
        return next((p for p in self._players if p.name == name), None)

    @property
    def crowned_index(self):
        """ Index of the crowned player """
        return self._players.index(self._crowned_player) if self._crowned_player else -1

    def find_by_id(self, player_id):
        """ Return player with given id or None """
        return next((p for p in self._players if p.player_id == player_id), None)

    def find_by_char(self, char):
        """ Return player that is a given char or None """
        return next((p for p in self._players if p.char == char), None)


class GameListener:
    def player_added(self, player: Player):
        pass

    def player_crowned(self, player: Player):
        pass

    def murder_announced(self, char: Character):
        pass

    def theft_announced(self, char: Character):
        pass


class Game(EventSource):
    def __init__(self, characters: Deck, districts: Deck):
        super().__init__()
        self._players = []
        self._bank = Bank()
        self._crowned_player = None
        self._turn = Turn(self)
        self._chars = None
        self._orig_chars = deepcopy(characters)
        self._districts = deepcopy(districts)

    def add_player(self, name, char=None, hand=None, city=None):
        """ Add new player to the game """
        player_id = len(self._players) + 1
        player = Player(player_id, self, char=char, hand=hand, city=city)
        player.name = name
        self._players.append(player)
        self.fire_event('player_added', player)
        return player

    @property
    def players(self):
        """ List of players """
        return PlayersProxy(self._players, self._crowned_player)

    @property
    def characters(self):
        """ Characters deck """
        return self._chars

    @property
    def districts(self):
        """ Districts deck """
        return self._districts

    @property
    def bank(self):
        """ Game's gold storage """
        return self._bank

    @property
    def crowned_player(self):
        """ Player who has the crown now """
        return self._crowned_player

    @crowned_player.setter
    def crowned_player(self, player):
        """ Player who has the crown now """
        assert player in self._players
        self._crowned_player = player
        self.fire_event('player_crowned', player)

    @property
    def turn(self):
        """ Per-turn info """
        return self._turn

    def new_turn(self):
        """ Prepare data for new turn """
        self._turn = Turn(self)
        self._chars = deepcopy(self._orig_chars)
