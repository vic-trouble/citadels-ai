from argparse import ArgumentParser
from collections import OrderedDict
import sys
assert sys.version_info[:2] >= (3, 7)

from ai.naive_bot import NaiveBotController
from ai.random_bot import RandomBotController
from citadels.cards import Card, Character, CharacterInfo, Color, District, DistrictInfo, all_chars, simple_districts, standard_chars
from citadels import commands
from citadels.game import Deck, Game, Player
from citadels.gameplay import CommandsSink, GameController, PlayerController
from citadels import shadow
from citadels import rules
from term import io


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

    elif isinstance(val, Card):
        return '?' if not val else help_str(val)

    elif isinstance(val, shadow.ShadowPlayer):
        return val.name

    elif isinstance(val, Player):
        return val.name

    else:
        return str(val)


def examine(my_player, game):
    unusable_chars = [CharacterInfo(char).name for char in game.turn.unused_chars if char]
    if unusable_chars:
        print('Unusable chars: {}'.format(', '.join(unusable_chars)))

    print('There are {} districts in the deck'.format(len(game.districts)))

    for player in game.players:
        king = '* ' if player == game.crowned_player else '  '
        values = {'king': king, 'plr': player.name, 'gold': player.gold,
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

            choices = ['.', '?']
            help = [('.', 'End turn'), ('?', 'Examine')]
            cmds = {'.': lambda: sink.end_turn(), '?': lambda: examine(player, game)}

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
        is_me = player.player_id == self._player.player_id
        card = DistrictInfo(district).name if is_me else 'a'
        print('{plr} has taken {card} card'.format(plr=player.name, card=card))

    def player_removed_card(self, player: Player, district: District):
        print('{plr} has removed {card} card'.format(plr=player.name, card=DistrictInfo(district).name))

    def player_built_district(self, player: Player, district: District):
        print('{plr} has built {district} ({total} in total)'.format(plr=player.name, district=DistrictInfo(district).name, total=len(player.city)))

    def player_lost_district(self, player: Player, district: District):
        print('{plr} has lost {card}'.format(plr=player.name, card=DistrictInfo(district).name))

    def turn_started(self):
        print('\n\n---------------------------------\nNew round starts!')
        examine(self._player, self._game)

    def _continue(self):
        io.dialog('Enter to continue', allow_empty=True)

    def turn_ended(self):
        game = self._game
        print('\nEnd of turn')
        if not game.players.find_by_char(game.turn.robbed_char):
            print('Nobody is robbed this turn!')
        if not game.players.find_by_char(game.turn.killed_char):
            print('Nobody is killed this turn!')
        self._continue()

    def player_killed(self, player: Player):
        print('{plr} is killed'.format(plr=player.name))
        self._continue()

    def player_robbed(self, player: Player, gold: int):
        thief = self._game.players.find_by_char(Character.Thief)
        print('{plr} is robbed by {thief} for {gold} gold'.format(plr=player.name, thief=thief.name, gold=gold))

    def player_plays(self, player: Player, char: Character):
        print('\n{plr} is {char}'.format(plr=player.name, char=help_str(char)))

    def player_played(self, player: Player):
        if player.player_id != self._player.player_id:
            self._continue()

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
    parser.add_argument('--bots', type=str, default='NRR')
    args = parser.parse_args()

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
