import pytest

from citadels.cards import Character
from citadels.game import Deck, Game, Player
from citadels.gameplay import CommandsSink, GameController, GamePlayConfig, PlayerController

from fixtures import game


class DummyPlayerController(PlayerController):
    def pick_char(self, char_deck: Deck, player: Player, game: Game):
        return Character.King if Character.King in char_deck.cards else char_deck.cards[0]

    def take_turn(self, player: Player, game: Game, sink: CommandsSink):
        if sink.possible_actions:
            sink.execute(sink.possible_actions[0])
        else:
            sink.end_turn()


class SpyPlayerController:
    def __init__(self):
        self.game = None
        self.possible_actions = None
        self.possible_chars = None

    def pick_char(self, char_deck: Deck, player: Player, game: Game):
        self.possible_chars = char_deck.cards
        return char_deck.cards[0]

    def take_turn(self, player: Player, game: Game, sink: CommandsSink):
        self.game = game
        if not self.possible_actions:
            self.possible_actions = list(sink.possible_actions)
        if sink.possible_actions:
            sink.execute(sink.possible_actions[0])
        else:
            sink.end_turn()


def test_start_game(game):
    # arrange
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
    assert game.crowned_player in (player1, player2)


def test_pick_chars(game):
    # arrange
    player1 = game.add_player('Player1')
    player2 = game.add_player('Player2')
    game.crowned_player = player2

    config = GamePlayConfig()
    config.turn_unused_faceup_chars = 2

    game_controller = GameController(game, config)
    controller1 = SpyPlayerController()
    game_controller.set_player_controller(player1, controller1)
    controller2 = SpyPlayerController()
    game_controller.set_player_controller(player2, controller2)

    game_controller.start_game()

    # act
    game_controller.start_turn()

    # assert
    # TURN-PICK
    assert player1.char is not None
    assert player2.char is not None
    # TURN-PICK-FIRST
    assert len(controller2.possible_chars) > len(controller1.possible_chars)

    # TURN-PICK-FACEDOWN
    assert len(game.turn.unused_chars) == 6

    # TURN-FACEUP
    assert sum(bool(char) for char in game.turn.unused_chars) == 2

    # TURN-FACEUP-KING
    assert Character.King not in game.turn.unused_chars


def test_take_turns(game):
    # arrange
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


@pytest.mark.skip(reason="shadowing is temporarily down")
def test_privates_are_not_exposed_to_bot(game):
    # arrange
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


def test_killed_char_misses_turn(game):
    # arrange
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


def test_thief_takes_gold_from_robbed_char(game):
    # arrange
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

    thief_gold = thief.gold
    victim_gold = victim.gold

    # act
    game_controller.take_turns()

    # assert
    turn_income = 2
    assert thief.gold == thief_gold + victim_gold + turn_income
    assert victim.gold == turn_income
