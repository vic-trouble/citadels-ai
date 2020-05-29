from collections import defaultdict
from enum import Enum, auto
from itertools import chain
import random

from citadels.cards import Card, Character, CharacterInfo, Deck, District, DistrictInfo
from citadels import commands
from citadels.event import EventSource, EventTransaction
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
        return tuple(self._possible_commands[CommandSpecifier.Action])

    @property
    def possible_abilities(self):
        return tuple(self._possible_commands[CommandSpecifier.Ability])

    @property
    def possible_builds(self):
        return tuple(self._possible_commands[CommandSpecifier.Build])

    @property
    def possible_income(self):
        return tuple(self._possible_commands[CommandSpecifier.Income])

    @property
    def all_possible_commands(self):
        return chain.from_iterable(self._possible_commands.values())

    def update(self):
        self._update()

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
            self._possible_commands[CommandSpecifier.Action] = rules.possible_actions(self._game)

        if not self._used_commands[CommandSpecifier.Ability]:
            char_workflow = rules.CharacterWorkflow(self._player.char)
            for ability in char_workflow.abilities:
                if isinstance(ability, commands.InteractiveCommand):
                    if not ability.ready and not ability.choices(self._player, self._game): # rare case when Destroy cannot be applied
                        continue
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
                build_command = commands.Build()
                if build_command.choices(self._player, self._game):
                    self._possible_commands[CommandSpecifier.Build].append(build_command)

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
        self.turn_unused_faceup_chars = None


class GamePlayEvents:
    def player_added(self, player: Player):
        pass

    def player_crowned(self, player: Player):
        pass

    def murder_announced(self, char: Character):
        pass

    def theft_announced(self, char: Character):
        pass

    def player_cashed_in(self, player: Player, amount: int):
        pass

    def player_withdrawn(self, player: Player, amount: int):
        pass

    def player_picked_char(self, player: Player, char: Character):
        pass

    def player_taken_card(self, player: Player, district: District):
        pass

    def player_taken_some_cards(self, player: Player, amount: int):
        pass

    def player_removed_card(self, player: Player, district: District):
        pass

    def player_built_district(self, player: Player, district: District):
        pass

    def player_lost_district(self, player: Player, district: District):
        pass

    def turn_started(self):
        pass

    def turn_ended(self):
        pass

    def player_killed(self, player: Player):
        pass

    def player_robbed(self, player: Player, gold: int):
        pass

    def player_plays(self, player: Player, char: Character):
        pass

    def player_played(self, player: Player):
        pass

    def player_swapped_hands(self, player, other_player):
        pass

    def player_replaced_hand(self, player, amount: int):
        pass


class GameplayState(Enum):
    START_GAME = auto()
    START_TURN = auto()
    TAKE_TURNS = auto()
    END_TURN = auto()
    END_GAME = auto()


class GameController(EventSource):
    def __init__(self, game: Game, config=None):
        super().__init__()
        self._game = game
        self._game.add_listener(self)
        self._config = config or GamePlayConfig()
        self._player_controllers = {}
        self._state = GameplayState.START_GAME

    def play(self):
        if self._state == GameplayState.START_GAME:
            self.start_game()
            self._state = GameplayState.START_TURN
        elif self._state == GameplayState.START_TURN:
            self.start_turn()
            self._state = GameplayState.TAKE_TURNS
        elif self._state == GameplayState.TAKE_TURNS:
            self.take_turns()
            self._state = GameplayState.END_GAME if self.game_over else GameplayState.END_TURN
        elif self._state == GameplayState.END_TURN:
            self.end_turn()
            self._state = GameplayState.START_TURN
        elif self._state == GameplayState.END_GAME:
            self.end_game()
            self._state = GameplayState.START_GAME

    def set_player_controller(self, player: Player, player_controller: PlayerController):
        assert player in self._game.players
        self._player_controllers[player.player_id] = player_controller
        player.add_listener(self)

    def player_controller(self, player: Player):
        assert player in self._game.players
        return self._player_controllers[player.player_id]

    def start_game(self):
        game = self._game
        if len(game.players) < 2:
            raise GameError('not enough players')

        game.new_game()

        for player in game.players:
            # START-CARDS
            with EventTransaction(self, 'player_taken_some_cards', player, 4):
                for _ in range(4):
                    player.take_card(game.districts.take_from_top())

            # START-GOLD
            player.cash_in(2)

        # START-CROWN
        if not game.crowned_player:
            game.crowned_player = random.choice(game.players)

    def start_turn(self):
        game = self._game
        game.new_turn()

        # TURN-FACEDOWN
        game.turn.drop_char(Card(game.characters.take_random()).facedown)

        # TURN-FACEUP
        if self._config.turn_unused_faceup_chars:
            faceup_cards = self._config.turn_unused_faceup_chars
        else:
            faceup_cards = {2: 2, 3: 2, 4: 2, 5: 1, 6: 0, 7: 0}[len(self._game.players)]
        for _ in range(faceup_cards):
            card = game.characters.take_random()

            # TURN-FACEUP-KING
            if card == Character.King:
                card = game.characters.take_random()
                game.characters.put_on_bottom(Character.King)

            game.turn.drop_char(card)

        self.fire_event('turn_started')

        # TURN-PICK-FIRST, TURN-PICK
        for player in game.players.order_by_char_selection():
            controller = self.player_controller(player)
            selected_char = controller.pick_char(game.characters, ShadowPlayer(player, me=True), ShadowGame(player, game))
            game.characters.take(selected_char)
            player.char = selected_char

        # TURN-PICK-FACEDOWN
        while game.characters:
            game.turn.drop_char(Card(game.characters.take_from_top()).facedown)

    def take_turns(self):
        if self.game_over:
            return

        game = self._game

        # TURN-CALL
        for player in game.players.order_by_take_turn():
            self.fire_event('player_plays', player, player.char)

            # KILLED
            if player.char == game.turn.killed_char:
                self.fire_event('player_killed', player)
                continue

            # ROBBED
            if player.char == game.turn.robbed_char:
                thief = game.players.find_by_char(Character.Thief)
                if player.gold:
                    # TODO: make tx
                    with EventTransaction(self, 'player_robbed', player, player.gold):
                        thief.cash_in(player.gold)
                        player.withdraw(player.gold)

            # KING-CROWNING
            if player.char == Character.King:
                game.crowned_player = player # fires event itself

            player_controller = self.player_controller(player)
            command_sink = CommandsSink(player, game)
            while not command_sink.done:
                player_controller.take_turn(ShadowPlayer(player, me=True), ShadowGame(player, game), command_sink)

            if rules.is_city_complete(player) and not game.turn.first_completer:
                game.turn.first_completer = player

            self.fire_event('player_played', player)

        # KING-KILLED
        if game.turn.killed_char == Character.King:
            king = game.players.find_by_char(Character.King)
            if king:
                game.crowned_player = king

    @property
    def game_over(self):
        return any(rules.is_city_complete(player) for player in self._game.players)

    def end_turn(self):
        for player in self._game.players:
            player.char = None
        self.fire_event('turn_ended')

    @property
    def winner(self):
        assert self.game_over
        # SCORE-WINNER
        by_score = defaultdict(list)
        for player in self._game.players:
            score = rules.score(player, self._game)
            by_score[score].append(player)

        max_score = max(by_score.keys())
        if len(by_score[max_score]) == 1:
            return by_score[max_score][0]

        by_pure_score = defaultdict(list)
        for player in by_score[max_score]:
            pure_score = rules.score(player, self._game, with_bonuses=False)
            by_pure_score[pure_score].append(player)

        max_pure_score = max(by_pure_score.keys())
        if len(by_pure_score[max_pure_score]) == 1:
            return by_pure_score[max_pure_score][0]

        by_gold = defaultdict(list)
        for player in by_pure_score[max_pure_score]:
            by_gold[player.gold].append(player)

        max_gold = max(by_gold.keys())
        return by_gold[max_gold][0]

    def end_game(self):
        self._game.reset()

    def player_added(self, player: Player):
        self.fire_event('player_added', player) # TODO: shadow everything!

    def player_crowned(self, player: Player):
        self.fire_event('player_crowned', player)

    def murder_announced(self, char: Character):
        self.fire_event('murder_announced', char)

    def theft_announced(self, char: Character):
        self.fire_event('theft_announced', char)

    def cashed_in(self, player: Player, amount: int):
        self.fire_event('player_cashed_in', player, amount)

    def withdrawn(self, player: Player, amount: int):
        self.fire_event('player_withdrawn', player, amount)

    def picked_char(self, player: Player, char: Character):
        self.fire_event('player_picked_char', player, char)

    def taken_card(self, player: Player, district: District):
        self.fire_event('player_taken_card', player, district)

    def removed_card(self, player: Player, district: District):
        self.fire_event('player_removed_card', player, district)

    def district_built(self, player: Player, district: District):
        self.fire_event('player_built_district', player, district)

    def district_lost(self, player: Player, district: District):
        self.fire_event('player_lost_district', player, district)

    def swapped_hands(self, player, other_player):
        self.fire_event('player_swapped_hands', player, other_player)

    def replaced_hand(self, player, amount: int):
        self.fire_event('player_replaced_hand', player, amount)
