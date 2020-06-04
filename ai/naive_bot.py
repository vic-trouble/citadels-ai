from collections import defaultdict
import random

from citadels import commands
from citadels.cards import Character, Deck, DistrictInfo, char_by_color
from citadels.game import Game, Player
from citadels.gameplay import CommandsSink, PlayerController
from citadels import rules


class Context:
    def __init__(self):
        self.builder_player = None
        self.rich_player = None
        self.hoarder_player = None
        self.other_players = []


class NaiveBotController(PlayerController):
    def pick_char(self, char_deck: Deck, player: Player, game: Game):
        """ Should return selected char card """
        other_players = tuple(p for p in game.players if p != player)

        # if one district left to build, pick Bishop (to protect from Warlord)
        if len(player.city) == 7 and Character.Bishop in char_deck: # TODO: bellfry is not accounted for
            return Character.Bishop

        # if everybody has some gold, pick Thief
        if player.gold <= 1 and all(p.gold >= 2 for p in game.players if p != player) and Character.Thief in char_deck:
            return Character.Thief

        # if there's the lead, pick Assassin or Warlord
        if any(len(p.city) >= 6 for p in other_players):
            if Character.Assassin in char_deck:
                return Character.Assassin
            elif Character.Warlord in char_deck:
                return Character.Warlord

        # if low on cards, pick Architect or Magician
        if Character.Architect in char_deck:
            return Character.Architect
        elif Character.Magician in char_deck:
            return Character.Magician

        bias = self._try_find_biased_color(player)
        if bias:
            color_char = char_by_color[bias]
            if color_char in char_deck:
                return color_char

        return random.choice(char_deck)

    def take_turn(self, player: Player, game: Game, sink: CommandsSink):
        command = self.decide(player, game, sink)
        if command:
            sink.execute(command)
        else:
            sink.end_turn()

    def create_context(self, player: Player, game: Game):
        # determine the leader (who's the threat)
        context = Context()

        context.builder_player = max(game.players, key=lambda p: (len(p.city), p == player))
        if not context.builder_player.city:
            context.builder_player = None

        context.rich_player = max(game.players, key=lambda p: p.gold)
        if not context.rich_player.gold:
            context.rich_player = None

        context.hoarder_player = max(game.players, key=lambda p: (len(p.hand), p == player))
        if not context.hoarder_player.hand:
            context.hoarder_player = None

        context.other_players = tuple(p for p in game.players if p != player)

        return context

    def decide(self, player: Player, game: Game, sink: CommandsSink):
        """ Should execute commands via sink """
        assert player in game.players

        context = self.create_context(player, game)

        # take income first
        if sink.possible_income:
            return sink.possible_income[0]

        # build
        if sink.possible_builds:
            build = sink.possible_builds[0]
            best_builds = sorted(build.choices(player, game), key=lambda d: DistrictInfo(d).cost, reverse=True)
            build.select(best_builds[0])
            return build

        # draw cards or take money
        if sink.possible_actions:
            take_gold = next(action for action in sink.possible_actions if isinstance(action, commands.CashIn))
            take_cards = next((action for action in sink.possible_actions if isinstance(action, commands.DrawSomeCards)), None)
            if not take_cards:
                return take_gold

            # architect may always take gold
            if player.char == Character.Architect:
                return take_gold

            if player.gold < 4:
                return take_gold

            best_card = next((card for card in take_cards.choices(player, game) if
                              rules.how_much_cost_to_build(card, player) <= player.gold and rules.can_be_built(card, player)), None)
            if not best_card:
                best_card = next((card for card in take_cards.choices(player, game) if rules.how_much_cost_to_build(card, player) <= player.gold), None)
                if not best_card:
                    best_card = take_cards.choices(player, game)[0]

            assert best_card
            take_cards.select(best_card)
            return take_cards

        # play powers
        if sink.possible_abilities:
            handlers = {
                Character.Thief: self.rob,
                Character.Warlord: self.destroy,
                Character.Assassin: self.kill,
                Character.Magician: self.do_tricks,
            }
            if player.char in handlers:
                command = handlers[player.char](sink.possible_abilities, context, player, game)
                if isinstance(command, commands.InteractiveCommand):
                    assert command.ready
                return command

    def rob(self, abilities, context: Context, player: Player, game: Game):
        rob = abilities[0]
        assert isinstance(rob, commands.Rob)

        targets = rob.choices(player, game)
        # merchant is a priority target
        if Character.Merchant in targets:
            rob.select(Character.Merchant)
        else:
            rob.select(random.choice(targets))
        return rob

    def destroy(self, abilities, context: Context, player: Player, game: Game):
        # cripple the lead
        destroy = abilities[0]
        assert isinstance(destroy, commands.Destroy)

        if len(context.builder_player.city) >= 6 and context.builder_player != player and context.builder_player.player_id in destroy.choices(player, game):
            destroy.select(context.builder_player.player_id)
            district = max(destroy.choices(player, game), key=lambda d: DistrictInfo(d).cost)
            destroy.select(district)
            return destroy

        # otherwise fire at second to lead
        for victim in sorted((pid for pid in destroy.choices(player, game) if pid != player.player_id), key=lambda pid: len(game.players.find_by_id(pid).city)):
            destroy.select(victim)
            if len(player.city) >= len(context.builder_player.city) or player.gold >= 4:
                district = max(destroy.choices(player, game), key=lambda d: DistrictInfo(d).cost)
            else:
                district = min(destroy.choices(player, game), key=lambda d: DistrictInfo(d).cost)
            destroy.select(district)
            return destroy

    def _try_find_biased_color(self, player: Player):
        colors = defaultdict(int)
        for district in player.city:
            colors[DistrictInfo(district).color] += 1
        if colors:
            first_color, first_count = max(colors.items(), key=lambda p: p[1])
            del colors[first_color]
            second_count = max(colors.values()) if colors else 0
            if first_count - second_count >= 2:
                return first_color

    def kill(self, abilities, context: Context, player: Player, game: Game):
        kill = abilities[0]
        assert isinstance(kill, commands.Kill)

        possible_chars = kill.choices(player, game)

        # try to guess the leader player by his colors
        if context.builder_player and context.builder_player != player:
            bias = self._try_find_biased_color(context.builder_player)
            if bias:
                color_char = char_by_color[bias]
                if color_char in possible_chars:
                    kill.select(color_char)
                    return kill

            # kill Architect if the leader is low on cards
            if len(context.builder_player.hand) <= 1:
                if Character.Architect in possible_chars:
                    kill.select(Character.Architect)
                    return kill

        # kill Merchant if anybody is low on gold
        if any(player.gold <= 1 for player in context.other_players) and Character.Merchant in possible_chars:
            kill.select(Character.Merchant)
            return kill

        # kill Architect if anybody is low on cards
        if any(len(player.hand) <= 1 for player in context.other_players) and Character.Architect in possible_chars:
            kill.select(Character.Architect)
            return kill

        # kill some poor random guy
        kill.select(random.choice(possible_chars))
        return kill

    def do_tricks(self, abilities, context: Context, player: Player, game: Game):
        swap_hands = next((c for c in abilities if isinstance(c, commands.SwapHands)), None)
        replace_hand = next((c for c in abilities if isinstance(c, commands.ReplaceHand)), None)

        # try to mess up the leader
        if swap_hands:
            if context.builder_player and context.builder_player != player:
                if len(context.builder_player.hand) - len(player.hand) >= 2:
                    swap_hands.select(context.builder_player.player_id)
                    return swap_hands

        # if low on cards, swap with the hoarder
        if swap_hands:
            if context.hoarder_player and context.builder_player != player:
                if len(player.hand) <= 1:
                    swap_hands.select(context.hoarder_player.player_id)
                    return swap_hands

        # if low build capability, replace hand
        if replace_hand:
            next_turn_gold = player.gold + 2
            buildable = []
            not_buildable = []
            for district in player.hand:
                if rules.how_much_cost_to_build(district, player) <= next_turn_gold and rules.can_be_built(district, player):
                    buildable.append(district)
                else:
                    not_buildable.append(district)
            if len(buildable) <= 1 and not_buildable:
                while not_buildable:
                    district = not_buildable.pop(0)
                    if district in replace_hand.choices(player, game):
                        replace_hand.select(district)
                return replace_hand
