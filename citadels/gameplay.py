from collections import defaultdict
from enum import Enum, auto

from citadels.cards import Card, Character, CharacterInfo, Deck, DistrictInfo
from citadels import commands
from citadels.game import Game, GameError, Player
from citadels import rules
from citadels.shadow import ShadowGame, ShadowPlayer


class CommandSpecifier(Enum):
    Action = auto()
    Ability = auto()
    Build = auto()
    Income = auto()


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
    def done(self):
        return self._done or not any(self._possible_commands.values())

    def end_turn(self):
        if self._used_commands[CommandSpecifier.Action]:
            self._done = True

    def execute(self, command: commands.Command):
        command.apply(self._player, self._game)
        self._used_commands[command.specifier].append(command)
        if command.restriction:
            if command.restriction & commands.Restriction.OnEndTurn:
                self._clear()
                return
        self._update()

    def _clear(self):
        self._possible_commands.clear()

    def _update(self):
        self._possible_commands.clear()

        if not self._used_commands[CommandSpecifier.Action]:
            self._possible_commands[CommandSpecifier.Action] = rules.possible_actions()

        if not self._used_commands[CommandSpecifier.Ability]:
            char_workflow = rules.CharacterWorkflow(self._player.char)
            for ability in char_workflow.abilities:
                if ability.restriction:
                    if ability.restriction & commands.Restriction.OnAfterAction:
                        if not self._used_commands[CommandSpecifier.Action]:
                            continue
                        if ability.restriction & commands.Restriction.Compulsory:
                            assert not isinstance(ability, commands.InteractiveCommand)
                            ability.apply(self._player, self._game)
                            self._used_commands[CommandSpecifier.Ability].append(ability)
                            continue
                    if ability.restriction & commands.Restriction.OnEndTurn:
                        if not self._used_commands[CommandSpecifier.Action]:
                            continue
                self._possible_commands[CommandSpecifier.Ability].append(ability)

        # BUILD
        if self._used_commands[CommandSpecifier.Action]:
            if len(self._used_commands[CommandSpecifier.Build]) < rules.how_many_districts_can_build(self._player):
                self._possible_commands[CommandSpecifier.Build].append(commands.Build())

        # INCOME
        if not self._used_commands[CommandSpecifier.Income]:
            color = CharacterInfo(self._player.char).color
            income = sum(DistrictInfo(district).color == color for district in self._player.city)
            if income:
                self._possible_commands[CommandSpecifier.Income].append(commands.CashIn(income))

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

        # CHAR-DECK
        game._orig_chars.shuffle()

        # DISTRICT-DECK
        game.districts.shuffle()

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
        for player in game.players.order_by_char_selection():
            controller = self.player_controller(player)
            selected_char = controller.pick_char(game.characters, ShadowPlayer(player), ShadowGame(game))
            game.characters.take(selected_char)
            player.char = selected_char

        # TURN-PICK-FACEDOWN
        while game.characters:
            game.turn.unused_chars.append(Card(game.characters.take_from_top()).facedown)

    def take_turns(self):
        game = self._game

        # TURN-CALL
        for player in game.players.order_by_take_turn():
            # KILLED
            if player.char == game.turn.killed_char:
                continue

            # ROBBED
            if player.char == game.turn.robbed_char:
                thief = game.players.find_by_char(Character.Thief)
                thief.cash_in(player.gold)
                player.withdraw(player.gold)

            # KING-CROWNING
            if player.char == Character.King:
                game.crowned_player = player

            player_controller = self.player_controller(player)
            command_sink = CommandsSink(player, game)
            while not command_sink.done:
                #action_available = bool(command_sink.possible_actions)
                player_controller.take_turn(ShadowPlayer(player, me=True), ShadowGame(game), command_sink)
                #if action_available and not command_sink.possible_actions:
                #    command = rules.CharacterWorkflow(player.char).after_action_command
                #    if command:
                #        command.apply(player, game)

        # KING-KILLED
        if game.turn.killed_char == Character.King:
            game.crowned_player = game.players.find_by_char(Character.King)
