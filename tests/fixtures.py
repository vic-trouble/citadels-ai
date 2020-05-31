import pytest

from citadels.cards import Character, Deck, simple_districts, standard_chars
from citadels.game import Game


@pytest.fixture
def game():
    return Game(Deck(standard_chars()), Deck(simple_districts()))


@pytest.fixture
def player(game):
    return game.add_player('Player')


@pytest.fixture
def king(game):
    player = game.add_player('King')
    player.char = Character.King
    return player


@pytest.fixture
def magician(game):
    player = game.add_player('Magician')
    player.char = Character.Magician
    return player


@pytest.fixture
def architect(game):
    player = game.add_player('Architect')
    player.char = Character.Architect
    return player


@pytest.fixture
def thief(game):
    player = game.add_player('Thief')
    player.char = Character.Thief
    return player


@pytest.fixture
def warlord(game):
    player = game.add_player('Warlord')
    player.char = Character.Warlord
    return player


@pytest.fixture
def assassin(game):
    player = game.add_player('Assassing')
    player.char = Character.Assassin
    return player


@pytest.fixture
def player1(game):
    return game.add_player('Player1')


@pytest.fixture
def player2(game):
    return game.add_player('Player2')


@pytest.fixture
def player3(game):
    return game.add_player('Player3')
