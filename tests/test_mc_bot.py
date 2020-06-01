from ai.mc_bot import evaluate
from citadels.cards import District

from fixtures import game, player1, player2


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
