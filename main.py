from argparse import ArgumentParser
from collections import OrderedDict
from itertools import chain
import string
import sys
assert sys.version_info[:2] >= (3, 7)

from ai.bot import BotController
from citadels.cards import Character, CharacterInfo, Color, District, DistrictInfo, all_chars, simple_districts, standard_chars
from citadels import commands
from citadels.game import Deck, Game, Player
from citadels.gameplay import CommandsSink, GameController, PlayerController
from term.io import dialog


def help_str(val):
    if isinstance(val, Character):
        info = CharacterInfo(val)
        if info.color:
            return '{name} ({color})'.format(name=info.name, color=help_str(info.color))
        else:
            return info.name
    elif isinstance(val, District):
        info = DistrictInfo(val)
        return '{name} ({cost} {color})'.format(name=info.name, cost=info.cost,
                                                color=help_str(info.color))
    elif isinstance(val, Color):
        return {
            Color.Red: 'R',
            Color.Blue: 'B',
            Color.Green: 'G',
            Color.Yellow: 'Y',
            Color.Purple: 'P',
        }[val]
    else:
        return str(val)


class TermPlayerController(PlayerController):
    def pick_char(self, char_deck: Deck, player: Player, game: Game):
        """ Should return selected char card """
        choices = ''.join(str(int(ch)) for ch in all_chars if ch in char_deck)
        help = OrderedDict({str(int(ch)): help_str(ch) for ch in all_chars if ch in char_deck})
        return Character(int(dialog('Pick a character for this round', choices=choices, help=help)))

    def take_turn(self, player: Player, game: Game, sink: CommandsSink):
        """ Should execute commands via sink """

        def make_exec(command: commands.Command):
            def do_exec(command: commands.Command):
                if isinstance(command, commands.InteractiveCommand):
                    all_marks = chain(string.ascii_lowercase, string.ascii_uppercase, string.digits, string.punctuation)
                    while command.choices(player, game):
                        ch_choices = []
                        ch_help = []
                        selection = {}
                        for choice in command.choices(player, game):
                            mark = next(iter(m for m in all_marks if m not in ch_choices))
                            selection[mark] = choice
                            ch_choices.append(mark)
                            ch_help.append((mark, help_str(choice)))
                        ch_inp = dialog('Select', choices=ch_choices, help=OrderedDict(ch_help))
                        command.select(selection[ch_inp])
                sink.execute(command)

            return lambda: do_exec(command)

        choices = ['.']
        help = [('.', 'End turn')]
        cmds = {'.': lambda: sink.end_turn()}

        for command in sink.all_possible_commands:
            all_marks = chain(string.ascii_lowercase, string.ascii_uppercase, string.digits, string.punctuation)
            mark = next(iter(m for m in all_marks if m not in cmds))
            cmds[mark] = make_exec(command)
            choices.append(mark)
            help.append((mark, command.help))
        inp = dialog('Your turn', choices=choices, help=OrderedDict(help))
        cmds[inp]()


class TermGamePlayListener:
    def __init__(self, game: Game):
        self._game = game

    def player_added(self, player: Player):
        print('{} has joined'.format(player.name))

    def player_crowned(self, player: Player):
        print('\n{} is the new King now!'.format(player.name))

    def murder_announced(self, char: Character):
        assassin = self._game.players.find_by_char(Character.Assassin)
        print('{ass} wants to kill {char}!'.format(ass=assassin.name, char=CharacterInfo(char).name))

    def theft_announced(self, char: Character):
        thief = self._game.players.find_by_char(Character.Thief)
        print('{thief} wants to rob {char}!'.format(thief=thief.name, char=CharacterInfo(char).name))

    def player_cashed_in(self, player: Player, amount: int):
        print('{plr} has taken {amount} gold ({total} in total)'.format(plr=player.name, amount=amount, total=player.gold))

    def player_withdrawn(self, player: Player, amount: int):
        print('{plr} has paid {amount} gold (left with {total})'.format(plr=player.name, amount=amount, total=player.gold))

    def player_picked_char(self, player: Player, char: Character):
        #print('{plr} is the {char}'.format(plr=player.name, char=CharacterInfo(char).name))
        pass

    def player_taken_card(self, player: Player, district: District):
        print('{plr} has taken {card} card'.format(plr=player.name, card=DistrictInfo(district).name))

    def player_removed_card(self, player: Player, district: District):
        print('{plr} has removed {card} card'.format(plr=player.name, card=DistrictInfo(district).name))

    def player_built_district(self, player: Player, district: District):
        print('{plr} has built {district} ({total} in total)'.format(plr=player.name, district=DistrictInfo(district).name, total=len(player.city)))

    def player_lost_district(self, player: Player, district: District):
        print('{plr} has lost {card}'.format(plr=player.name, card=DistrictInfo(district).name))

    def turn_started(self):
        print('\n\n---------------------------------\nNew round starts!')
        unusable_chars = [CharacterInfo(char).name for char in self._game.turn.unused_chars if char]
        if unusable_chars:
            print('Unusable chars: {}'.format(', '.join(unusable_chars)))

        for player in self._game.players:
            king = '* ' if player == self._game.crowned_player else ''
            print('{king}{plr} with {gold} gold, hand={hand}, city={city}'.format(king=king, plr=player.name, hand=[help_str(d) for d in player.hand], city=[help_str(d) for d in player.city], gold=player.gold))

    def player_killed(self, player: Player):
        print('\n{plr} is killed'.format(plr=player.name))

    def player_robbed(self, player: Player, gold: int):
        thief = self._game.players.find_by_char(Character.Thief)
        print('\n{plr} is robbed by {thief} for {gold} gold'.format(plr=player.name, thief=thief.name, gold=gold))

    def player_plays(self, player: Player, char: Character):
        print('\n{plr} is {char}'.format(plr=player.name, char=help_str(char)))

    def player_swapped_hands(self, player, other_player):
        if player.char == Character.Magician:
            print('{plr} swapped hands with {other}'.format(plr=player.name, other=other_player.name))

    def player_replaced_hand(self, player, amount: int):
        print('{plr} replaced {amount} cards'.format(plr=player.name, amount=amount))

    def player_taken_some_cards(self, player: Player, amount: int):
        print('{plr} has taken {amount} cards'.format(plr=player.name, amount=amount))


def main():
    parser = ArgumentParser()
    parser.add_argument('--name', type=str, default='')
    parser.add_argument('--players', type=int, default=0)
    args = parser.parse_args()

    num_players = args.players
    name = args.name

    if not num_players:
        num_players = int(dialog('Enter number of players (2..7)', '234567'))
    if not name:
        name = dialog('Enter your name', lambda n: n.strip() != '')

    game = Game(Deck(standard_chars()), Deck(simple_districts()))
    game_controller = GameController(game)
    game_controller.add_listener(TermGamePlayListener(game))

    assert 2 <= num_players <= 7
    player = game.add_player(name)
    game_controller.set_player_controller(player, TermPlayerController())
    for i in range(num_players - 1):
        bot = game.add_player('bot{}'.format(i + 1))
        game_controller.set_player_controller(bot, BotController())

    game_controller.start_game()

    while not game_controller.game_over:
        game_controller.start_turn()
        game_controller.take_turns()
        game_controller.end_turn()


if __name__ == '__main__':
    main()
