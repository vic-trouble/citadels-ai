"""
TODO:
- factor our fixtures
"""

from citadels.cards import Character, standard_chars, simple_districts
from citadels.game import Deck, Game, Player
from citadels.gameplay import CommandsSink, GameController, GamePlayConfig, PlayerController


class DummyPlayerController(PlayerController):
    def pick_char(self, char_deck: Deck, player: Player, game: Game):
        return Character.King if Character.King in char_deck.cards else char_deck.cards[0]

    def take_turn(self, player: Player, game: Game, sink: CommandsSink):
        sink.end_turn()


class SpyPlayerController(DummyPlayerController):
    def __init__(self):
        super().__init__()
        self.possible_actions = []

    def pick_char(self, char_deck: Deck, player: Player, game: Game):
        return char_deck.cards[0]

    def take_turn(self, player: Player, game: Game, sink: CommandsSink):
        self.possible_actions = sink.possible_actions
        sink.execute(self.possible_actions[0])


def test_start_game():
    # arrange
    characters = Deck(standard_chars())
    districts = Deck(simple_districts())

    game = Game(characters, districts)

    player1 = game.add_player('Player1')
    player2 = game.add_player('Player2')

    game_controller = GameController(game)
    game_controller.set_player_controller(player1, DummyPlayerController())
    game_controller.set_player_controller(player2, DummyPlayerController())

    # act
    game_controller.start_game()

    # assert
    # START-CARDS
    assert len(player1.hand) == 4
    assert len(player2.hand) == 4

    # START-GOLD
    assert player1.gold == 2
    assert player2.gold == 2

    # START-CROWN
    assert game.crowned_player == player1


def test_pick_chars():
    # arrange
    characters = Deck(standard_chars())
    districts = Deck(simple_districts())

    game = Game(characters, districts)

    player1 = game.add_player('Player1')
    player2 = game.add_player('Player2')
    game.crowned_player = player2

    config = GamePlayConfig()
    config.turn_unused_faceup_chars = 2

    game_controller = GameController(game, config)
    game_controller.set_player_controller(player1, DummyPlayerController())
    game_controller.set_player_controller(player2, DummyPlayerController())

    game_controller.start_game()

    # act
    game_controller.start_turn()

    # assert
    # TURN-PICK
    assert player1.char is not None
    # TURN-PICK-FIRST
    assert player2.char == Character.King

    # TURN-PICK-FACEDOWN
    assert len(game.turn.unused_chars) == 6

    # TURN-FACEUP
    assert sum(bool(char) for char in game.turn.unused_chars) == 2

    # TURN-FACEUP-KING
    assert Character.King not in game.turn.unused_chars


def test_take_turns():
    characters = Deck(standard_chars())
    districts = Deck(simple_districts())

    game = Game(characters, districts)

    player1 = game.add_player('Player1')
    player2 = game.add_player('Player2')

    game_controller = GameController(game)
    spy_controller = SpyPlayerController()
    game_controller.set_player_controller(player1, spy_controller)
    game_controller.set_player_controller(player2, DummyPlayerController())

    game_controller.start_game()
    game_controller.start_turn()

    # act
    game_controller.take_turns()

    # assert
    assert len(spy_controller.possible_actions) == 2
