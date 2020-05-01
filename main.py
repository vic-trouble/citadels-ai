from collections import OrderedDict
import sys
assert sys.version_info[:2] >= (3, 7)

from ai.bot import BotController
from citadels.cards import Character, CharacterInfo, all_chars, simple_districts, standard_chars
from citadels.game import Deck, Game, Player
from citadels.gameplay import CommandsSink, GameController, PlayerController
from term.tabulate import tabulate


def dialog(prolog, choices=None, help=None):
    def is_iterable(obj):
        try:
            iter(obj)
            return True
        except TypeError:
            return False

    while True:
        if help:
            print(prolog)
            print('\n'.join(tabulate('{k}: {v}'.format(k=k, v=v) for k, v in help.items())))
            print('> ', end='')
        else:
            print(prolog + ': ', end='')
        inp = input()
        if not choices:
            return inp
        if is_iterable(choices):
            if inp in choices:
                return inp
        elif callable(choices):
            if choices(inp):
                return True
        else:
            raise TypeError('Invalid choices')


class TermPlayerController(PlayerController):
    def pick_char(self, char_deck: Deck, player: Player, game: Game):
        """ Should return selected char card """
        choices = ''.join(str(int(ch)) for ch in all_chars if ch in char_deck)
        help = OrderedDict({str(int(ch)): CharacterInfo(ch).name for ch in all_chars if ch in char_deck})
        return Character(int(dialog('Pick a character for this round', choices=choices, help=help)))

    def take_turn(self, player: Player, game: Game, sink: CommandsSink):
        """ Should execute commands via sink """
        raise NotImplementedError()


def main():
    num_players = 2
    name = 'V'

    if not num_players:
        num_players = int(dialog('Enter number of players (2..8)', '2345678'))
    if not name:
        name = dialog('Enter your name', lambda n: n.strip() != '')

    game = Game(Deck(standard_chars()), Deck(simple_districts()))
    game_controller = GameController(game)
    player = game.add_player(name)
    game_controller.set_player_controller(player, TermPlayerController())
    for i in range(num_players - 1):
        bot = game.add_player('bot{}'.format(i + 1))
        game_controller.set_player_controller(bot, BotController())

    game_controller.start_game()

    game_controller.start_turn()
    game_controller.take_turns()


if __name__ == '__main__':
    main()
