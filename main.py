from argparse import ArgumentParser
from collections import OrderedDict
import sys
assert sys.version_info[:2] >= (3, 7)

from colorama import Fore, Style, init as init_colorama

from ai.naive_bot import NaiveBotController
from ai.random_bot import RandomBotController
from citadels.cards import Card, Character, CharacterInfo, Color, District, DistrictInfo, all_chars, simple_districts, standard_chars
from citadels import commands
from citadels.game import Deck, Game, Player
from citadels.gameplay import CommandsSink, GameController, PlayerController
from citadels import shadow
from citadels import rules
from term import io


COLORING = True


def color(color: Color):
    return {
        Color.Blue: Fore.LIGHTBLUE_EX + Style.BRIGHT,
        Color.Green: Fore.LIGHTGREEN_EX + Style.BRIGHT,
        Color.Red: Fore.LIGHTRED_EX + Style.BRIGHT,
        Color.Yellow: Fore.LIGHTYELLOW_EX + Style.BRIGHT,
        Color.Purple: Fore.LIGHTMAGENTA_EX + Style.BRIGHT,
        None: Fore.LIGHTWHITE_EX + Style.BRIGHT,
    }[color]


def help_str(val):
    if isinstance(val, Character):
        info = CharacterInfo(val)
        if COLORING:
            return f'{color(info.color)}{info.name}{Style.RESET_ALL}'
        else:
            if info.color:
                return '{name} ({color})'.format(name=info.name, color=help_str(info.color))
            else:
                return info.name

    elif isinstance(val, District):
        info = DistrictInfo(val)
        if COLORING:
            return f'{color(info.color)}{info.name}{Style.RESET_ALL} ({info.cost})'
        else:
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

    elif isinstance(val, Card):
        return '?' if not val else help_str(val)

    elif isinstance(val, shadow.ShadowPlayer):
        if COLORING:
            return f'{Fore.LIGHTWHITE_EX}{Style.BRIGHT}{val.name}{Style.RESET_ALL}'
        else:
            return val.name

    elif isinstance(val, Player):
        if COLORING:
            return f'{Fore.LIGHTWHITE_EX}{Style.BRIGHT}{val.name}{Style.RESET_ALL}'
        else:
            return val.name

    elif isinstance(val, int):
        if COLORING:
            return f'{Fore.LIGHTWHITE_EX}{Style.BRIGHT}{val}{Style.RESET_ALL}'
        else:
            return str(int)

    else:
        if COLORING:
            return f'{Fore.LIGHTWHITE_EX}{Style.BRIGHT}{val}{Style.RESET_ALL}'
        else:
            return str(val)


def examine(my_player, game):
    unusable_chars = [help_str(char) for char in game.turn.unused_chars if char]
    if unusable_chars:
        print('Unusable chars: {}'.format(', '.join(unusable_chars)))

    print('There are {} districts in the deck'.format(len(game.districts)))

    for player in game.players:
        if player == game.crowned_player:
            if COLORING:
                king = f'{Fore.LIGHTYELLOW_EX}{Style.BRIGHT}*{Style.RESET_ALL} '
            else:
                king = '* '
        else:
            king = '  '
        values = {'king': king, 'plr': help_str(player.name), 'gold': help_str(player.gold),
                  'city': ', '.join(help_str(d) for d in player.city), 'city_size': len(player.city)}

        is_me = player.player_id == my_player.player_id
        values['hand'] = ', '.join(help_str(d) if is_me else '?' for d in my_player.hand)

        known_char = is_me and player.char
        if not known_char:
            if bool(player.char):
                player_ids = [p.player_id for p in game.players.order_by_take_turn()]
                player_index = player_ids.index(player.player_id)
                my_player_index = player_ids.index(my_player.player_id)
                known_char = player_index < my_player_index
        values['char'] = ' ({})'.format(help_str(player.char)) if known_char else ''
        values['score'] = rules.score(player, game, with_bonuses=True)

        print('{king}[{score}] {plr}{char} with {gold} gold | hand=[{hand}] | city({city_size})=[{city}]'.format(**values))


class TermPlayerController(PlayerController):
    def pick_char(self, char_deck: Deck, player: Player, game: Game):
        """ Should return selected char card """
        chars = [ch for ch in all_chars if ch in char_deck]
        desc = [help_str(ch) for ch in chars]
        keys = io.assign_keys(desc)
        help = OrderedDict({key: io.emphasize(help_str(ch), key) for key, ch in zip(keys, chars)})
        inp = io.dialog('Pick a character for this round', choices=''.join(keys), help=help)
        index = keys.index(inp)
        return chars[index]

    def take_turn(self, player: Player, game: Game, sink: CommandsSink):
        """ Should execute commands via sink """
        cancelled = True

        def make_select(command: commands.InteractiveCommand, choice):
            return lambda: command.select(choice)

        def make_exec(command: commands.Command):
            def do_exec(command: commands.Command):
                if isinstance(command, commands.InteractiveCommand):
                    done = False

                    def finish():
                        nonlocal done
                        done = True

                    def cancel():
                        command.cancel(player, game)
                        nonlocal cancelled
                        cancelled = True

                    while command.choices(player, game) and not done and not cancelled:
                        ch_choices = ['?', '!']
                        ch_help = [('?', 'Examine'), ('!', 'Cancel')]
                        selection = {'?': lambda: examine(player, game), '!': cancel}
                        if command.ready:
                            ch_choices.append('.')
                            ch_help.append(('.', 'Done'))
                            selection['.'] = finish
                        all_choices = command.choices(player, game)
                        desc = [help_str(choice) for choice in all_choices]
                        keys = io.assign_keys(desc)
                        for choice, choice_desc, key in zip(all_choices, desc, keys):
                            selection[key] = make_select(command, choice)
                            ch_choices.append(key)
                            ch_help.append((key, io.emphasize(choice_desc, key)))
                        ch_inp = io.dialog('Select', choices=ch_choices, help=OrderedDict(ch_help))
                        selection[ch_inp]()

                    if cancelled:
                        return

                sink.execute(command)

            return lambda: do_exec(command)

        while cancelled:
            cancelled = False

            choices = ['?']
            help = [('?', 'Examine')]
            cmds = {'?': lambda: examine(player, game)}

            if sink.can_end_turn:
                choices.append('.')
                help.append(('.', 'End turn'))
                cmds['.'] = sink.end_turn

            all_commands = list(sink.all_possible_commands)
            desc = [command.help for command in all_commands]
            keys = io.assign_keys(desc)
            for command, command_desc, key in zip(all_commands, desc, keys):
                cmds[key] = make_exec(command)
                choices.append(key)
                help.append((key, io.emphasize(command_desc, key)))

            inp = io.dialog('Your turn', choices=choices, help=OrderedDict(help))
            cmds[inp]()

            if cancelled:
                sink.update()


class TermGamePlayListener:
    def __init__(self, player: Player, game: Game):
        self._player = player
        self._game = game
        self._skip_continue = False
        self._always_skip_continue = False

    def player_added(self, player: Player):
        print('{} has joined'.format(help_str(player.name)))

    def player_crowned(self, player: Player):
        print('\n{} is the new King now!'.format(help_str(player.name)))

    def murder_announced(self, char: Character):
        assassin = self._game.players.find_by_char(Character.Assassin)
        print('{ass} wants to kill the {char}!'.format(ass=help_str(assassin.name), char=help_str(char)))

    def theft_announced(self, char: Character):
        thief = self._game.players.find_by_char(Character.Thief)
        print('{thief} wants to rob the {char}!'.format(thief=help_str(thief.name), char=help_str(char)))

    def player_cashed_in(self, player: Player, amount: int, source: str):
        if source:
            print('{plr} has taken {amount} gold ({source})'.format(plr=help_str(player.name), amount=help_str(amount), source=source))
        else:
            print('{plr} has taken {amount} gold'.format(plr=help_str(player.name), amount=help_str(amount)))

    def player_withdrawn(self, player: Player, amount: int):
        print('{plr} has paid {amount} gold'.format(plr=help_str(player.name), amount=help_str(amount)))

    def player_picked_char(self, player: Player, char: Character):
        #print('{plr} is the {char}'.format(plr=player.name, char=help_str(char)))
        pass

    def player_taken_card(self, player: Player, district: District):
        is_me = player.player_id == self._player.player_id
        card = help_str(district) if is_me else 'a'
        print('{plr} has taken {card} card'.format(plr=help_str(player.name), card=card))

    def player_removed_card(self, player: Player, district: District):
        print('{plr} has removed {card} card'.format(plr=help_str(player.name), card=help_str(district)))

    def player_built_district(self, player: Player, district: District):
        print('{plr} has built {district}'.format(plr=help_str(player.name), district=help_str(district)))

    def player_lost_district(self, player: Player, district: District):
        print('{plr} has lost {card}'.format(plr=help_str(player.name), card=help_str(district)))

    def turn_started(self):
        print('\n\n---------------------------------\nNew round starts!')
        examine(self._player, self._game)
        if not self._always_skip_continue:
            self._skip_continue = False

    def _continue(self):
        if self._skip_continue:
            return

        choices = ['?', '.', '!']
        help = [('Enter', 'Continue'), ('?', 'Examine'), ('.', 'Skip'), ('!', 'Always skip')]
        #cmds = {'?': lambda: examine(self._player, self._game)}
        while True:
            inp = io.dialog('', choices=choices, help=OrderedDict(help), allow_empty=True)
            if not inp:
                break
            if inp == '?':
                examine(self._player, self._game)
            elif inp == '.':
                self._skip_continue = True
                break
            elif inp == '!':
                self._skip_continue = True
                self._always_skip_continue = True
                break

    def turn_ended(self):
        game = self._game
        print('\nEnd of turn')
        if not game.players.find_by_char(game.turn.robbed_char):
            print('Nobody is robbed this turn!')
        if not game.players.find_by_char(game.turn.killed_char):
            print('Nobody is killed this turn!')
        self._continue()

    def player_killed(self, player: Player):
        print('{plr} is killed'.format(plr=help_str(player.name)))
        self._continue()

    def player_robbed(self, player: Player, gold: int):
        thief = self._game.players.find_by_char(Character.Thief)
        print('{plr} is robbed by {thief} for {gold} gold'.format(plr=help_str(player.name), thief=help_str(thief.name), gold=help_str(gold)))

    def player_plays(self, player: Player, char: Character):
        print('\n{plr} is the {char}'.format(plr=help_str(player.name), char=help_str(char)))
        if player.player_id == self._player.player_id:
            examine(self._player, self._game)

    def player_played(self, player: Player):
        print('{plr} has finished their turn'.format(plr=help_str(player.name)))
        if player.player_id != self._player.player_id:
            self._continue()

    def player_swapped_hands(self, player, other_player):
        if player.char == Character.Magician:
            print('{plr} swapped hands with {other}'.format(plr=help_str(player.name), other=help_str(other_player.name)))

    def player_replaced_hand(self, player, amount: int):
        print('{plr} replaced {amount} cards'.format(plr=help_str(player.name), amount=amount))

    def player_taken_some_cards(self, player: Player, amount: int):
        print('{plr} has taken {amount} cards'.format(plr=help_str(player.name), amount=amount))


def main():
    parser = ArgumentParser()
    parser.add_argument('--name', type=str, default='')
    parser.add_argument('--bots', type=str, default='NRR')
    parser.add_argument('--no-color', action='store_true', default=False)
    args = parser.parse_args()

    global COLORING
    COLORING = not args.no_color
    if COLORING:
        init_colorama()

    bots = args.bots
    name = args.name

    if not name:
        name = io.dialog('Enter your name', lambda n: n.strip() != '')

    game = Game(Deck(standard_chars()), Deck(simple_districts()))
    game_controller = GameController(game)

    assert 1 <= len(bots) <= 3
    assert all(b in 'NR' for b in bots)

    player = game.add_player(name)
    game_controller.set_player_controller(player, TermPlayerController())

    game_controller.add_listener(TermGamePlayListener(player, game))

    bot_factory = {'R': RandomBotController, 'N': NaiveBotController}
    for i, b in enumerate(bots):
        bot = game.add_player('bot{}'.format(i + 1))
        game_controller.set_player_controller(bot, bot_factory[b]())

    while not game_controller.game_over:
        game_controller.play()

    print('\n----------------------\nGame over!\n')
    for player in game.players:
        print('{plr} scored {score}'.format(plr=player.name, score=rules.score(player, game)))
    print('Winner is {plr}'.format(plr=game_controller.winner.name))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nBye')
