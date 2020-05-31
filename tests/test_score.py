import pytest

from citadels.cards import District
from citadels.gameplay import GameController
from citadels import rules

from fixtures import game


def test_score_is_cost_of_the_city(game):
    # arrange
    player = game.add_player('Player', city=[District.Watchtower, District.Palace])

    # act
    score = rules.score(player, game)

    # assert
    assert score == 1 + 5


def test_bonus_for_all_colors(game):
    # arrange
    player = game.add_player('Player', city=[District.Watchtower, District.Tavern, District.Temple, District.Manor])

    # act
    score = rules.score(player, game)

    # assert
    bonus = 3
    assert score == 1 + 1 + 1 + 3 + bonus


def test_bonus_for_completing_city(game):
    # arrange
    player = game.add_player('Player', city=[District.Watchtower]*8)

    # act
    score = rules.score(player, game)

    # assert
    bonus = 2
    assert score == 8 + bonus


def test_bonus_for_completing_city_first(game):
    # arrange
    player = game.add_player('Player', city=[District.Watchtower]*8)

    game.turn.first_completer = player

    # act
    score = rules.score(player, game)

    # assert
    bonus = 4
    assert score == 8 + bonus


def test_winner_with_most_score(game):
    # arrange
    player1 = game.add_player('Player1', city=[District.Watchtower]*8)
    player2 = game.add_player('Player2', city=[District.Watchtower]*7)

    game_controller = GameController(game)

    game.turn.first_completer = player1

    # act
    winner = game_controller.winner

    # assert
    assert winner == player1


def test_winner_with_most_score_without_bonuses_if_tie(game):
    # arrange
    player1 = game.add_player('Player1', city=[District.Watchtower]*8)
    player2 = game.add_player('Player2', city=[District.Palace, District.Cathedral, District.TradingPost])

    game_controller = GameController(game)

    game.turn.first_completer = player1

    assert rules.score(player1, game) == 12
    assert rules.score(player2, game) == 12

    # act
    winner = game_controller.winner

    # assert
    assert winner == player2


def test_winner_with_most_gold_if_double_tie(game):
    # arrange
    player1 = game.add_player('Player1', city=[District.Watchtower]*8)
    player2 = game.add_player('Player2', city=[District.Tavern]*8)

    player1.cash_in(9)
    player2.cash_in(10)

    game_controller = GameController(game)

    assert rules.score(player1, game) == 10
    assert rules.score(player1, game, with_bonuses=False) == 8
    assert rules.score(player2, game) == 10
    assert rules.score(player2, game, with_bonuses=False) == 8

    # act
    winner = game_controller.winner

    # assert
    assert winner == player2
