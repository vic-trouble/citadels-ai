import random

from citadels import commands
from citadels.game import Deck, Game, Player
from citadels.gameplay import CommandsSink, PlayerController
from citadels.rules import score


PROB_END_TURN = 0.1


def per_player_evaluate(player, game):
    return score(player, game) * 2 + \
           player.gold


def evaluate(player, game):
    return per_player_evaluate(player, game) - max(per_player_evaluate(p, game) for p in game.players if p.player_id != player.player_id)


class MonteCarloBotController(PlayerController):
    def pick_char(self, char_deck: Deck, player: Player, game: Game):
        """ Should return selected char card """
        raise NotImplementedError()

    def take_turn(self, player: Player, game: Game, sink: CommandsSink):
        """ Should execute commands via sink """
        raise NotImplementedError()

    def make_plan(self, player: Player, game: Game, sim_limit=1000):
        best_plan = None
        best_scoring = 0
        for _ in range(sim_limit):
            test_game = game.clone()
            test_player = test_game.players.find_by_id(player.player_id)
            sink = CommandsSink(test_player, test_game)
            plan = []
            while not sink.done:
                command = random.choice(list(sink.all_possible_commands))
                if isinstance(command, commands.InteractiveCommand):
                    while not command.ready:
                        command.select(random.choice(command.choices(test_player, test_game)))
                plan.append(command)
                sink.execute(command)
                if sink.can_end_turn and random.random() < PROB_END_TURN:
                    sink.end_turn()
            scoring = evaluate(test_player, test_game)
            if best_plan is None or scoring > best_scoring:
                best_plan = plan
                best_scoring = scoring
        return best_plan
