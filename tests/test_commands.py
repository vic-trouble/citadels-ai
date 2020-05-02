import pytest

from citadels.cards import Character, Deck, District, simple_districts, standard_chars
from citadels import commands
from citadels.game import Game
from citadels.shadow import ShadowGame, ShadowPlayer


@pytest.fixture
def game():
    characters = Deck(standard_chars())
    districts = Deck(simple_districts())

    game = Game(characters, districts)
    game.new_turn()
    return game


@pytest.fixture
def player(game):
    return game.add_player('Player1')


def test_cash_in(player, game):
    # arrange
    command = commands.CashIn(10)

    # act
    command.apply(player, game)

    # assert
    assert player.gold == 10


def test_draw_cards(player, game):
    # arrange
    command = commands.DrawCards(draw=2, keep=1)

    # act
    command.apply(player, game)

    # assert
    assert len(player.hand) == 2 # TODO: should be 1; not implemented


def test_kill(player, game):
    # arrange
    command = commands.Kill()

    # act
    choices = command.choices(ShadowPlayer(player, me=True), ShadowGame(game))
    assert choices
    assert Character.Assassin not in choices

    command.select(Character.King)
    assert not command.choices(ShadowPlayer(player, me=True), ShadowGame(game))

    command.apply(player, game)

    # assert
    assert game.turn.killed_char == Character.King


def test_rob(player, game):
    # arrange
    command = commands.Rob()

    game.turn.killed_char = Character.King

    # act
    choices = command.choices(ShadowPlayer(player, me=True), ShadowGame(game))
    assert choices
    assert Character.Assassin not in choices
    assert Character.King not in choices

    command.select(Character.Bishop)
    assert not command.choices(ShadowPlayer(player, me=True), ShadowGame(game))

    command.apply(player, game)

    # assert
    assert game.turn.robbed_char == Character.Bishop


def test_swap_hands(game):
    # arrange
    player1 = game.add_player('Player1')
    player1.hand = [District.Manor]

    player2 = game.add_player('Player2')
    player2.hand = [District.Tavern, District.Cathedral]

    command = commands.SwapHands()

    # act
    choices = command.choices(ShadowPlayer(player1, me=True), ShadowGame(game))
    assert [p.name for p in choices] == ['Player2']

    command.select(player2)
    assert not command.choices(ShadowPlayer(player1, me=True), ShadowGame(game))

    command.apply(player1, game)

    # assert
    assert player1.hand == [District.Tavern, District.Cathedral]
    assert player2.hand == [District.Manor]


def test_replace_hands(player, game):
    # arrange
    player.hand = [District.Cathedral, District.Tavern]

    command = commands.ReplaceHand()

    num_districts = len(game.districts)

    # act
    assert command.choices(ShadowPlayer(player, me=True), ShadowGame(game)) == [District.Cathedral, District.Tavern]

    command.select(District.Cathedral)
    assert command.choices(ShadowPlayer(player, me=True), ShadowGame(game)) == [District.Tavern]

    command.apply(player, game)

    # assert
    assert player.hand != [District.Cathedral, District.Tavern]
    assert len(player.hand) == 2
    assert len(game.districts) == num_districts


def test_destroy(game):
    # arrange
    player1 = game.add_player('Player1')
    player1.city = [District.Manor]

    player2 = game.add_player('Player2')
    player2.city = [District.Tavern, District.Cathedral]

    command = commands.Destroy()

    # act
    assert [p.name for p in command.choices(ShadowPlayer(player1, me=True), ShadowGame(game))] == ['Player1', 'Player2']
    command.select(player2)

    assert command.choices(ShadowPlayer(player1, me=True), ShadowGame(game)) == [District.Tavern, District.Cathedral]
    command.select(District.Tavern)

    assert not command.choices(ShadowPlayer(player1, me=True), ShadowGame(game))
    command.apply(player1, game)

    # assert
    assert player2.city == [District.Cathedral]


def test_build(game):
    # arrange
    player = game.add_player('Player1')
    player.hand = [District.Manor, District.Palace]
    player.city = []
    player.cash_in(4)

    # act
    command = commands.Build()
    assert command.choices(player, game) == [District.Manor]

    command.select(District.Manor)
    command.apply(player, game)

    # assert
    assert player.hand == [District.Palace]
    assert player.city == [District.Manor]
    assert player.gold == 1


def test_take_crown(game):
    # arrange
    player = game.add_player('Player1')
    command = commands.TakeCrown()

    # act
    command.apply(player, game)

    # assert
    assert game.crowned_player == player
