from collections import defaultdict
from copy import deepcopy

from citadels.cards import Character, Deck


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


class Player:
    def __init__(self, player_id, game):
        self.name = ''
        self._id = player_id
        self._game = game
        self._char = None
        self._hand = []
        self._city = []

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

    @property
    def hand(self):
        return self._hand

    def cash_in(self, amount):
        """ Give some gold """
        return self._bank_account.cash_in(amount)

    def withdraw(self, amount):
        """ Remove some gold """
        return self._bank_account.withdraw(amount)

    def __repr__(self):
        return 'Player("{}")'.format(self.name)

    @property
    def char(self):
        return self._char

    @char.setter
    def char(self, value):
        self._char = value

    @property
    def city(self):
        return list(self._city)


class Turn:
    def __init__(self):
        self._unused_chars = []
        self.killed_char = None
        self.robbed_char = None

    def drop_char(self, char: Character):
        """ Remove character from playable set """
        self._unused_chars.append(char)

    @property
    def unused_chars(self):
        return self._unused_chars


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

    def by_char_selection(self):
        """ Players in order of character selection """
        index = self.crowned_index
        if index == -1:
            return list(self._players)
        else:
            return self._players[index:] + self._players[:index]

    def by_take_turn(self):
        """ Players in order of making their turn """
        return list(sorted(self._players, key=lambda p: p.char))

    def find_by_name(self, name):
        """ Return first player with given name or None """
        return next((p for p in self._players if p.name == name), None)

    @property
    def crowned_index(self):
        """ Index of the crowned player """
        return self._players.index(self._crowned_player) if self._crowned_player else -1


class Game:
    def __init__(self, characters: Deck, districts: Deck):
        self._players = []
        self._bank = Bank()
        self._crowned_player = None
        self._turn = None
        self._chars = None
        self._orig_chars = deepcopy(characters)
        self._districts = deepcopy(districts)

    def add_player(self, name):
        """ Add new player to the game """
        player_id = len(self._players) + 1
        player = Player(player_id, self)
        player.name = name
        self._players.append(player)
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

    @property
    def turn(self):
        """ Per-turn info """
        return self._turn

    def new_turn(self):
        """ Prepare data for new turn """
        self._turn = Turn()
        self._chars = deepcopy(self._orig_chars)
