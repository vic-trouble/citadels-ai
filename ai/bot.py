import random

from citadels.commands import InteractiveCommand
from citadels.game import Deck, Game, Player
from citadels.gameplay import CommandsSink, PlayerController


class BotController(PlayerController):
    def pick_char(self, char_deck: Deck, player: Player, game: Game):
        """ Should return selected char card """
        return random.choice(char_deck)

    def take_turn(self, player: Player, game: Game, sink: CommandsSink):
        """ Should execute commands via sink """
        command = None
        for source in (sink.possible_income, sink.possible_actions, sink.possible_builds,
                       sink.possible_abilities, sink.possible_final):
            if source:
                command = random.choice(source)
                break

        if isinstance(command, InteractiveCommand):
            while command.choices(player, game):
                command.select(random.choice(command.choices(player, game)))

        if command:
            sink.execute(command)
        else:
            sink.end_turn()
