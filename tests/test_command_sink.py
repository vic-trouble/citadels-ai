import pytest

from citadels.cards import Character, Deck, District, simple_districts, standard_chars
from citadels import commands
from citadels.game import Game
from citadels.gameplay import CommandsSink

@pytest.fixture
def game():
    characters = Deck(standard_chars())
    districts = Deck(simple_districts())
    return Game(characters, districts)


def test_possible_actions(game):
    # arrange
    player = game.add_player('Player')
    player.char = Character.King

    # act
    sink = CommandsSink(player, game)

    # assert
    assert sink.possible_actions == [commands.CashIn(2), commands.DrawCards(draw=2, keep=1)]


def test_possible_income(game):
    # arrange
    player = game.add_player('Player')
    player.char = Character.Warlord
    player.city = [District.Prison, District.Watchtower, District.TradingPost]

    # act
    sink = CommandsSink(player, game)

    # assert
    assert sink.possible_income == [commands.CashIn(2)]


def test_possible_build(game):
    # arrange
    player = game.add_player('Player')
    player.char = Character.King
    player.cash_in(2)
    player.hand = [District.Tavern, District.Fortress]

    # assert
    sink = CommandsSink(player, game)
    assert not sink.possible_builds

    sink.execute(sink.possible_actions[0])
    assert sink.possible_builds == [commands.Build()]


def test_assassin_abilities(game):
    # arrange
    player = game.add_player('Player')
    player.char = Character.Assassin

    # act
    sink = CommandsSink(player, game)

    # assert
    assert sink.possible_abilities == [commands.Kill()]


def test_thief_abilities(game):
    # arrange
    player = game.add_player('Player')
    player.char = Character.Thief

    # act
    sink = CommandsSink(player, game)

    # assert
    assert sink.possible_abilities == [commands.Rob()]


def test_magician_abilities(game):
    # arrange
    player = game.add_player('Player')
    player.char = Character.Magician

    # act
    sink = CommandsSink(player, game)

    # assert
    assert sink.possible_abilities == [commands.SwapHands(), commands.ReplaceHand()]


def test_warlord_abilities(game):
    # arrange
    player = game.add_player('Player')
    player.char = Character.Warlord

    # assert
    sink = CommandsSink(player, game)
    assert not sink.possible_abilities

    sink.execute(sink.possible_actions[0])
    assert sink.possible_abilities == [commands.Destroy()]


def test_warlord_ability_is_final(game):
    # arrange
    player = game.add_player('Player')
    player.char = Character.Warlord
    player.cash_in(2)
    player.hand = [District.Tavern, District.Fortress]
    player.city = [District.Watchtower]

    # act
    sink = CommandsSink(player, game)
    sink.execute(sink.possible_actions[0])

    destroy = sink.possible_abilities[0]
    while destroy.choices(player, game):
        destroy.select(destroy.choices(player, game)[0])
    sink.execute(destroy)

    # assert
    assert not sink.possible_builds

# TODO: test merchant ability?
# TODO: test architect ability?
