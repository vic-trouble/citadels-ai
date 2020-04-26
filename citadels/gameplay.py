from collections import defaultdict
from enum import Enum, auto

from citadels.cards import Card, Character, Deck
from citadels.commands import Command
from citadels.game import Game, GameError, Player
from citadels import rules


class CommandSpecifier(Enum):
    Action = auto()
    Ability = auto()
    Build = auto()
    Income = auto()
    Final = auto()


class CommandsSink:
    def __init__(self, player: Player, game: Game):
        self._player = player
        self._game = game
        self._done = False
        self._possible_commands = defaultdict(list)
        self._used_commands = defaultdict(list)
        self._update()

    @property
    def possible_actions(self):
        return self._possible_commands[CommandSpecifier.Action]

    @property
    def possible_abilities(self):
        return self._possible_commands[CommandSpecifier.Ability]

    @property
    def possible_builds(self):
        return self._possible_commands[CommandSpecifier.Build]

    @property
    def possible_income(self):
        return self._possible_commands[CommandSpecifier.Income]

    @property
    def possible_final(self):
        return self._possible_commands[CommandSpecifier.Final]

    @property
    def done(self):
        return self._done or not any(self._possible_commands.values())

    def end_turn(self):
        self._done = True

    def execute(self, command: Command):
        command.apply(self._player, self._game)
        self._used_commands[command.specifier].append(command)
        self._update()

    def _update(self):
        self._possible_commands[CommandSpecifier.Action] = rules.possible_actions() if \
            not self._used_commands[CommandSpecifier.Action] else []

        self._assign_specifiers()

    def _assign_specifiers(self):
        for specifier, commands in self._possible_commands.items():
            for command in commands:
                setattr(command, 'specifier', specifier)


class PlayerController:
    def pick_char(self, char_deck: Deck, player: Player, game: Game):
        """ Should return selected char card """
        raise NotImplementedError()

    def take_turn(self, player: Player, game: Game, sink: CommandsSink):
        """ Should execute commands via sink """
        raise NotImplementedError()


class GamePlayConfig:
    def __init__(self):
        self.turn_unused_faceup_chars = 1


class GameController:
    def __init__(self, game: Game, config=None):
        self._game = game
        self._config = config or GamePlayConfig()
        self._player_controllers = {}

    def set_player_controller(self, player: Player, player_controller: PlayerController):
        assert player in self._game.players
        self._player_controllers[player.player_id] = player_controller

    def player_controller(self, player: Player):
        assert player in self._game.players
        return self._player_controllers[player.player_id]

    def start_game(self):
        game = self._game
        if len(game.players) < 2:
            raise GameError('not enough players')

        # START-CROWN
        if not game.crowned_player:
            game.crowned_player = game.players[0]

        for player in game.players:
            # START-CARDS
            for _ in range(4):
                player.hand.append(game.districts.take_from_top())

            # START-GOLD
            player.cash_in(2)

    def start_turn(self):
        game = self._game
        game.new_turn()

        # TURN-FACEDOWN
        game.turn.unused_chars.append(Card(game.characters.take_random()).facedown)

        # TURN-FACEUP
        for _ in range(self._config.turn_unused_faceup_chars):
            card = game.characters.take_random()

            # TURN-FACEUP-KING
            if card == Character.King:
                card = game.characters.take_random()
                game.characters.put_on_bottom(Character.King)

            game.turn.unused_chars.append(card)

        # TURN-PICK-FIRST, TURN-PICK
        for player in game.players.by_char_selection():
            selected_char = self.player_controller(player).pick_char(self._game.characters, player, game)
            self._game.characters.take(selected_char)
            player.char = selected_char

        # TURN-PICK-FACEDOWN
        while game.characters:
            game.turn.unused_chars.append(Card(game.characters.take_from_top()).facedown)

    def take_turns(self):
        # TURN-CALL
        for player in self._game.players.by_take_turn():
            player_controller = self.player_controller(player)
            command_sink = CommandsSink(player, self._game)
            while not command_sink.done:
                player_controller.take_turn(player, self._game, command_sink)
