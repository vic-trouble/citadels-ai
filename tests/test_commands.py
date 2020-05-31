import pytest

from citadels.cards import Character, District
from citadels import commands
from citadels.shadow import ShadowGame, ShadowPlayer

from fixtures import game, player


def test_cash_in(player, game):
    # arrange
    command = commands.CashIn(10)

    # act
    command.apply(player, game)

    # assert
    assert player.gold == 10


def test_draw_some_cards(player, game):
    # arrange
    command = commands.DrawSomeCards(draw=2, keep=1)

    num_districts = len(game.districts)

    # act
    command.select(command.choices(player, game)[0])
    command.apply(player, game)

    # assert
    assert len(player.hand) == 1
    assert len(game.districts) == num_districts - 1


def test_draw_some_cards_cancel(player, game):
    # arrange
    districts = tuple(game.districts)

    command = commands.DrawSomeCards(draw=2, keep=1)

    # act
    command.select(command.choices(player, game)[0])
    command.cancel(player, game)

    # assert
    assert len(player.hand) == 0
    assert districts == tuple(game.districts)


def test_draw_some_cards_cancel_without_draw(player, game):
    # arrange
    districts = tuple(game.districts)

    command = commands.DrawSomeCards(draw=2, keep=1)

    # act
    command.cancel(player, game)

    # assert
    assert len(player.hand) == 0
    assert districts == tuple(game.districts)


def test_draw_cards(player, game):
    # arrange
    command = commands.DrawCards(2)

    num_districts = len(game.districts)

    # act
    command.apply(player, game)

    # assert
    assert len(player.hand) == 2
    assert len(game.districts) == num_districts - 2


def test_kill(player, game):
    # arrange
    command = commands.Kill()

    game.turn.drop_char(Character.Architect)

    # act
    choices = command.choices(ShadowPlayer(player, me=True), ShadowGame(player, game))
    assert choices
    assert Character.Assassin not in choices
    assert Character.Architect not in choices

    command.select(Character.King)
    assert not command.choices(ShadowPlayer(player, me=True), ShadowGame(player, game))

    command.apply(player, game)

    # assert
    assert game.turn.killed_char == Character.King


def test_rob(player, game):
    # arrange
    command = commands.Rob()

    game.turn.drop_char(Character.Architect)
    game.turn.killed_char = Character.King

    # act
    choices = command.choices(ShadowPlayer(player, me=True), ShadowGame(player, game))
    assert choices
    assert Character.Assassin not in choices
    assert Character.King not in choices
    assert Character.Thief not in choices
    assert Character.Architect not in choices

    command.select(Character.Bishop)
    assert not command.choices(ShadowPlayer(player, me=True), ShadowGame(player, game))

    command.apply(player, game)

    # assert
    assert game.turn.robbed_char == Character.Bishop


def test_swap_hands(game):
    # arrange
    player1 = game.add_player('Player1', hand=[District.Manor])
    player2 = game.add_player('Player2', hand=[District.Tavern, District.Cathedral])

    command = commands.SwapHands()

    # act
    choices = command.choices(ShadowPlayer(player1, me=True), ShadowGame(player, game))
    assert [p.name for p in choices] == ['Player2']

    command.select(player2)
    assert not command.choices(ShadowPlayer(player1, me=True), ShadowGame(player, game))

    command.apply(player1, game)

    # assert
    assert player1.hand == (District.Tavern, District.Cathedral,)
    assert player2.hand == (District.Manor,)


def test_replace_hands(game):
    # arrange
    player = game.add_player('Player', hand=[District.Cathedral, District.Tavern, District.Cathedral])

    command = commands.ReplaceHand()

    num_districts = len(game.districts)

    # act
    assert command.choices(ShadowPlayer(player, me=True), ShadowGame(player, game)) == [District.Cathedral, District.Tavern, District.Cathedral]

    command.select(District.Cathedral)
    assert command.choices(ShadowPlayer(player, me=True), ShadowGame(player, game)) == [District.Tavern, District.Cathedral]

    command.apply(player, game)

    # assert
    assert len(player.hand) == 3
    assert list(player.hand)[:2] == [District.Tavern, District.Cathedral]
    assert player.hand[2] != District.Cathedral

    assert len(game.districts) == num_districts


def test_destroy(game):
    # arrange
    num_districts = len(game.districts)

    player1 = game.add_player('Player1', city=[District.Manor])
    player1.cash_in(3)

    player2 = game.add_player('Player2', city=[District.Docks, District.Cathedral])

    command = commands.Destroy()

    # act
    assert [p.name for p in command.choices(ShadowPlayer(player1, me=True), ShadowGame(player1, game))] == ['Player1', 'Player2']
    command.select(player2)

    assert command.choices(ShadowPlayer(player1, me=True), ShadowGame(player1, game)) == [District.Docks]
    command.select(District.Docks)

    assert not command.choices(ShadowPlayer(player1, me=True), ShadowGame(player1, game))
    command.apply(player1, game)

    # assert
    assert player1.gold == 1
    assert player2.city == (District.Cathedral,)
    assert len(game.districts) == num_districts + 1
    assert game.districts[-1] == District.Docks


def test_build(game):
    # arrange
    player = game.add_player('Player1', hand=[District.Manor, District.Palace])
    player.cash_in(4)

    # act
    command = commands.Build()
    assert command.choices(player, game) == [District.Manor]

    command.select(District.Manor)
    command.apply(player, game)

    # assert
    assert player.hand == (District.Palace,)
    assert player.city == (District.Manor,)
    assert player.gold == 1


def test_take_crown(game):
    # arrange
    player = game.add_player('Player1')
    command = commands.TakeCrown()

    # act
    command.apply(player, game)

    # assert
    assert game.crowned_player == player
