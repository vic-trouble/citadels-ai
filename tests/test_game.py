from citadels.cards import Character
from citadels.game import Deck, Game


def test_players_char_selection_order():
    # arrange
    game = Game(Deck([]), Deck([]))

    player1 = game.add_player('Player1')
    player2 = game.add_player('Player2')
    player3 = game.add_player('Player3')

    # act
    game.crowned_player = player2

    # assert: CROWN
    assert game.players.by_char_selection() == [player2, player3, player1]


def test_players_take_turn_order():
    # arrange
    game = Game(Deck([]), Deck([]))

    player1 = game.add_player('Player1')
    player2 = game.add_player('Player2')
    player3 = game.add_player('Player3')

    player1.char = Character.King
    player2.char = Character.Thief
    player3.char = Character.Assassin

    # assert: CROWN
    assert game.players.by_take_turn() == [player3, player2, player1]
