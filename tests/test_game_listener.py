import pytest
from unittest.mock import Mock

from citadels.cards import Character

from fixtures import game, player


@pytest.fixture
def listener(game):
    listener = Mock()
    game.add_listener(listener)
    return listener


def test_player_added(game, listener):
    # arrange
    added_player = None

    def save_added_player(player):
        nonlocal added_player
        added_player = player

    listener.player_added = Mock(side_effect=save_added_player)

    # act
    game.add_player('Player1')

    # assert
    assert added_player


def test_player_crowned(game, player, listener):
    # arrange
    crowned_player = None

    def save_crowned_player(player):
        nonlocal crowned_player
        crowned_player = player

    listener.player_crowned = Mock(side_effect=save_crowned_player)

    # act
    game.crowned_player = player

    # assert
    assert crowned_player


def test_murder_announced(game, listener):
    # arrange
    to_be_killed = None

    def save_char(char):
        nonlocal to_be_killed
        to_be_killed = char

    listener.murder_announced = Mock(side_effect=save_char)

    # act
    game.turn.killed_char = Character.King

    # assert
    assert to_be_killed == Character.King


def test_theft_announced(game, listener):
    # arrange
    to_be_robbed = None

    def save_char(char):
        nonlocal to_be_robbed
        to_be_robbed = char

    listener.theft_announced = Mock(side_effect=save_char)

    # act
    game.turn.robbed_char = Character.King

    # assert
    assert to_be_robbed == Character.King
