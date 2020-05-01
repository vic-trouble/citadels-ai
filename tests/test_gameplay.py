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
        self.possible_actions = None
        self.possible_abilities = None

    def pick_char(self, char_deck: Deck, player: Player, game: Game):
        return char_deck.cards[0]

    def take_turn(self, player: Player, game: Game, sink: CommandsSink):
        self.possible_actions = list(sink.possible_actions)
        self.possible_abilities = list(sink.possible_abilities)
        self.game = game
        sink.end_turn()


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


def test_pick_chars(): # TODO: fails at times
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
    assert spy_controller.possible_abilities


def test_privates_are_not_exposed_to_bot():
    # arrange
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
    game = spy_controller.game
    assert not any(bool(district) for district in game.districts)
    assert game.crowned_player in game.players
    another_player = game.players.find_by_name('Player2')
    assert not any(bool(district) for district in another_player.hand)
    assert all(bool(district) for district in another_player.city)  # TODO: not verifiable
    assert another_player.gold
    assert not hasattr(another_player, 'game')


def test_killed_char_misses_turn():
    # arrange
    characters = Deck(standard_chars())
    districts = Deck(simple_districts())

    game = Game(characters, districts)

    assassing = game.add_player('Player1')
    victim = game.add_player('Player2')

    game_controller = GameController(game)
    game_controller.set_player_controller(assassing, DummyPlayerController())
    game_controller.set_player_controller(victim, victim_controller := SpyPlayerController())

    game_controller.start_game()
    game_controller.start_turn()

    assassing.char = Character.Assassin
    victim.char = Character.King
    game.turn.killed_char = Character.King

    # act
    game_controller.take_turns()

    # assert
    assert not victim_controller.possible_actions


def test_thief_takes_gold_from_robbed_char():
    # arrange
    characters = Deck(standard_chars())
    districts = Deck(simple_districts())

    game = Game(characters, districts)

    thief = game.add_player('Player1')
    victim = game.add_player('Player2')
    victim.cash_in(10)

    game_controller = GameController(game)
    game_controller.set_player_controller(thief, DummyPlayerController())
    game_controller.set_player_controller(victim, DummyPlayerController())

    game_controller.start_game()
    game_controller.start_turn()

    thief.char = Character.Thief
    victim.char = Character.King
    game.turn.robbed_char = Character.King

    # act
    game_controller.take_turns()

    # assert
    assert thief.gold == 10 + 2 + 2
    assert victim.gold == 0
