import pytest

from ai.mc_bot import MonteCarloBotController, evaluate
from citadels.cards import Character, District
from citadels import commands

from fixtures import game, player1, player2


@pytest.fixture
def bot():
    return MonteCarloBotController()


def test_better_eval_if_more_score(game, player1, player2):
    # arrange
    player1.build_district(District.Palace)
    player2.build_district(District.Docks)

    eval1 = evaluate(player1, game)
    eval2 = evaluate(player2, game)

    # assert
    assert eval1 > eval2


def test_better_eval_if_rival_has_less_score(game, player1, player2):
    # arrange
    player1.build_district(District.Palace)
    player2.build_district(District.Docks)

    eval_before = evaluate(player1, game)

    # act
    player2.destroy_district(District.Docks)
    eval_after = evaluate(player1, game)

    # assert
    assert eval_after > eval_before


def test_better_eval_if_more_gold(game, player1, player2):
    # arrange
    player1.cash_in(10)
    player2.cash_in(5)

    eval1 = evaluate(player1, game)
    eval2 = evaluate(player2, game)

    # assert
    assert eval1 > eval2


def test_mc_bot_build_finishing_district(game, bot, player1):
    # arrange
    player = game.add_player('bot', char=Character.King, hand=[District.Palace, District.Watchtower], city=[District.Docks]*7)
    player.cash_in(10)

    # act
    plan = bot.make_plan(player, game, sim_limit=100)

    # assert
    assert commands.Build(district=District.Palace) in plan


def test_mc_bot_destroys_rival_district(game, bot):
    # arrange
    player = game.add_player('bot', char=Character.Warlord, hand=[District.Palace, District.Watchtower], city=[District.Docks]*6)
    player.cash_in(10)

    leader = game.add_player('leader', char=Character.King, hand=[District.Palace], city=[District.Docks]*6 + [District.Cathedral])
    game.add_player('second', char=Character.King, hand=[District.Palace], city=[District.Docks]*6)

    # act
    plan = bot.make_plan(player, game, sim_limit=500)

    # assert
    assert commands.Destroy(target_id=leader.player_id, card=District.Cathedral) in plan
