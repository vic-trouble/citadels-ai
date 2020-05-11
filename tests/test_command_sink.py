# TODO: test king ability?

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
    player = game.add_player('Player', char=Character.King)

    # act
    sink = CommandsSink(player, game)

    # assert
    assert sink.possible_actions == (commands.CashIn(2), commands.DrawSomeCards(draw=2, keep=1))


def test_possible_income(game):
    # arrange
    city = [District.Prison, District.Watchtower, District.TradingPost]
    player = game.add_player('Player', char=Character.Warlord, city=city)

    # act
    sink = CommandsSink(player, game)

    # assert
    assert sink.possible_income == (commands.CashIn(2),)


def test_possible_build(game):
    # arrange
    player = game.add_player('Player', char=Character.King, hand=[District.Tavern, District.Fortress])
    player.cash_in(2)

    # assert
    sink = CommandsSink(player, game)
    assert not sink.possible_builds

    sink.execute(sink.possible_actions[0])
    assert sink.possible_builds == (commands.Build(),)


def test_assassin_abilities(game):
    # arrange
    player = game.add_player('Player', char=Character.Assassin)

    # act
    sink = CommandsSink(player, game)

    # assert
    assert sink.possible_abilities == (commands.Kill(),)


def test_thief_abilities(game):
    # arrange
    player = game.add_player('Player', char=Character.Thief)

    # act
    sink = CommandsSink(player, game)

    # assert
    assert sink.possible_abilities == (commands.Rob(),)


def test_magician_abilities(game):
    # arrange
    player = game.add_player('Player', char=Character.Magician)
    player.take_card(District.Watchtower)

    victim = game.add_player('Victim', char=Character.King)
    victim.take_card(District.Docks)

    # act
    sink = CommandsSink(player, game)

    # assert
    assert sink.possible_abilities == (commands.SwapHands(), commands.ReplaceHand())


def test_warlord_abilities(game):
    # arrange
    player = game.add_player('Player', char=Character.Warlord)

    victim = game.add_player('Victim', char=Character.King)
    victim.build_district(District.Docks)

    # assert
    sink = CommandsSink(player, game)
    assert not sink.possible_abilities

    sink.execute(sink.possible_actions[0])
    assert sink.possible_abilities == (commands.Destroy(),)


def test_warlord_ability_is_final(game):
    # arrange
    hand = [District.Tavern, District.Fortress]
    city = [District.Watchtower]
    player = game.add_player('Player', char=Character.Warlord, hand=hand, city=city)
    player.cash_in(2)

    # act
    sink = CommandsSink(player, game)
    sink.execute(sink.possible_actions[0])

    destroy = sink.possible_abilities[0]
    while destroy.choices(player, game):
        destroy.select(destroy.choices(player, game)[0])
    sink.execute(destroy)

    # assert
    assert not sink.possible_builds


def test_merchant_ability(game):
    # arrange
    player = game.add_player('Player', char=Character.Merchant)
    player.cash_in(1)

    # act
    sink = CommandsSink(player, game)

    draw_cards = next(iter(action for action in sink.possible_actions if isinstance(action, commands.DrawSomeCards)))
    draw_cards.select(draw_cards.choices(player, game)[0])
    sink.execute(draw_cards)

    # assert
    assert player.gold == 2


def test_architect_ability(game):
    # arrange
    player = game.add_player('Player', char=Character.Architect, hand=[District.Watchtower])

    # act
    sink = CommandsSink(player, game)
    sink.execute(next(iter(action for action in sink.possible_actions if isinstance(action, commands.CashIn))))

    # assert
    assert len(player.hand) == 3


def test_sink_is_done_when_end_turn_called(game):
    # arrange
    player = game.add_player('Player', char=Character.Assassin)

    # act
    sink = CommandsSink(player, game)
    sink.execute(sink.possible_actions[0])
    sink.end_turn()

    # assert
    assert sink.done


def test_cannot_end_turn_without_action_taken(game):
    # arrange
    player = game.add_player('Player', char=Character.Assassin)

    # act
    sink = CommandsSink(player, game)
    sink.end_turn()

    # assert
    assert not sink.done


def test_income_may_be_taken_before_action(game):
    # arrange
    player = game.add_player('Player', char=Character.Warlord, city=[District.Prison])

    # act
    sink = CommandsSink(player, game)

    # assert
    assert sink.possible_income


def test_income_must_be_taken_after_action(game):
    # arrange
    player = game.add_player('Player', char=Character.Warlord, hand=[District.Watchtower])
    player.cash_in(10)

    # act
    sink = CommandsSink(player, game)
    sink.execute(sink.possible_actions[0])

    # assert
    assert sink.possible_builds


def test_builds_cannot_be_made_before_action(game):
    # arrange
    player = game.add_player('Player', char=Character.Warlord, hand=[District.Watchtower])
    player.cash_in(10)

    # act
    sink = CommandsSink(player, game)

    # assert
    assert not sink.possible_builds


def test_builds_can_be_made_after_action(game):
    # arrange
    player = game.add_player('Player', char=Character.Warlord, city=[District.Prison], hand=[District.Watchtower])
    player.cash_in(10)

    # act
    sink = CommandsSink(player, game)
    sink.execute(sink.possible_actions[0])

    # assert
    assert sink.possible_builds
