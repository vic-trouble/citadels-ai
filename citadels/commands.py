from enum import IntFlag, auto

from citadels.cards import Character, all_chars
from citadels.event import EventTransaction
from citadels.game import Game, Player
from citadels import rules


class Restriction(IntFlag):
    OnStartTurn = auto()
    OnEndTurn = auto()
    OnAfterAction = auto()
    Compulsory = auto()


class Command:
    def __init__(self, restriction=0):
        self.restriction = restriction

    def apply(self, player: Player, game: Game):
        raise NotImplementedError()

    @property
    def help(self):
        raise NotImplementedError()


class InteractiveCommand(Command):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def choices(self, player: Player, game: Game):
        raise NotImplementedError()

    def select(self, choice):
        raise NotImplementedError()

    def apply(self, player: Player, game: Game):
        raise NotImplementedError()

    @property
    def help(self):
        raise NotImplementedError()

    @property
    def ready(self):
        raise NotImplementedError()

    def cancel(self, player: Player, game: Game):
        # too little commands need cancel, so nop is the reasonable default
        pass


class CashIn(Command):
    def __init__(self, amount, source=None, **kwargs):
        super().__init__(**kwargs)
        self._amount = amount
        self._source = source

    def apply(self, player: Player, game: Game):
        player.cash_in(self._amount, self._source)

    def __repr__(self):
        return 'CashIn({})'.format(self._amount)

    def __eq__(self, other):
        return isinstance(other, CashIn) and self._amount == other._amount

    @property
    def help(self):
        if self._source:
            return f'Take {self._amount} gold ({self._source})'
        else:
            return f'Take {self._amount} gold'


class DrawCards(Command):
    def __init__(self, amount, **kwargs):
        super().__init__(**kwargs)
        self._draw = amount

    def apply(self, player: Player, game: Game):
        for _ in range(self._draw):
            if not game.districts:
                break
            player.take_card(game.districts.take_from_top())

    def __repr__(self):
        return 'DrawCards({draw})'.format(draw=self._draw)

    def __eq__(self, other):
        return isinstance(other, DrawCards) and self._draw == other._draw

    @property
    def help(self):
        return 'Draw {} cards'.format(self._draw)


class DrawSomeCards(InteractiveCommand):
    def __init__(self, draw=2, keep=1, **kwargs):
        super().__init__(**kwargs)
        self._draw = draw
        self._keep = keep
        assert 0 < self._keep <= self._draw
        self._orig_card_taken = []
        self._cards_taken = []
        self._cards_to_keep = []

    def choices(self, player: Player, game: Game):
        if not self._cards_taken:
            self._cards_taken = [game.districts.take_from_top() for _ in range(self._draw)]
            self._orig_card_taken = tuple(self._cards_taken)
        if len(self._cards_to_keep) < self._keep:
            return self._cards_taken
        else:
            return []

    def select(self, choice):
        assert choice in self._cards_taken
        self._cards_taken.remove(choice)
        self._cards_to_keep.append(choice)

    def apply(self, player: Player, game: Game):
        assert self._cards_to_keep
        for card in self._cards_to_keep:
            player.take_card(card)
        for card in self._cards_taken:
            game.districts.put_on_bottom(card)

    def __repr__(self):
        return 'DrawSomeCards(draw={draw}, keep={keep})'.format(draw=self._draw, keep=self._keep)

    def __eq__(self, other):
        return isinstance(other, DrawSomeCards) and (self._draw, self._keep) == (other._draw, other._keep)

    @property
    def help(self):
        return 'Draw {} cards'.format(self._draw) + (' ({} to keep)'.format(self._keep) if self._keep != self._draw else '')

    @property
    def ready(self):
        return len(self._cards_to_keep) == self._keep

    def cancel(self, player: Player, game: Game):
        # TODO: mm... rollback a transaction?
        for card in reversed(self._orig_card_taken):
            game.districts.put_on_top(card)


class Kill(InteractiveCommand):
    def __init__(self, char=None, **kwargs):
        super().__init__(**kwargs)
        self._char = char

    def choices(self, player: Player, game: Game):
        if self._char:
            return []
        else:
            return [char for char in all_chars if char != Character.Assassin and char not in game.turn.unused_chars]

    def select(self, choice):
        self._char = choice

    def apply(self, player: Player, game: Game):
        assert self._char
        assert not game.turn.killed_char
        game.turn.killed_char = self._char

    def __repr__(self):
        return 'Kill({})'.format(self._char)

    def __eq__(self, other):
        return isinstance(other, Kill) and self._char == other._char

    @property
    def help(self):
        return 'Kill'

    @property
    def ready(self):
        return bool(self._char)


class Rob(InteractiveCommand):
    def __init__(self, char=None, **kwargs):
        super().__init__(**kwargs)
        self._char = char

    def choices(self, player: Player, game: Game):
        if self._char:
            return []
        else:
            cant_rob = [Character.Thief, Character.Assassin, game.turn.killed_char] + list(game.turn.unused_chars)
            return [char for char in all_chars if char not in cant_rob]

    def select(self, choice):
        self._char = choice

    def apply(self, player: Player, game: Game):
        assert self._char
        assert not game.turn.robbed_char
        game.turn.robbed_char = self._char

    def __repr__(self):
        return 'Rob({})'.format(self._char)

    def __eq__(self, other):
        return isinstance(other, Rob) and self._char == other._char

    @property
    def help(self):
        return 'Rob'

    @property
    def ready(self):
        return bool(self._char)


class SwapHands(InteractiveCommand):
    def __init__(self, target_id=None, **kwargs):
        super().__init__(**kwargs)
        self._target_id = target_id

    def choices(self, player: Player, game: Game):
        if self._target_id:
            return []
        return [p.player_id for p in game.players if p.player_id != player.player_id]

    def select(self, choice):
        self._target_id = choice

    def apply(self, player: Player, game: Game):
        assert self._target_id
        player1 = game.players.find_by_id(player.player_id)
        player2 = game.players.find_by_id(self._target_id)

        with EventTransaction(player1, 'swapped_hands', player1, player2), EventTransaction(player2, 'swapped_hands', player2, player1):
            p1_cards = tuple(player1.hand)
            for card in player2.hand:
                player2.remove_card(card)
                player1.take_card(card)
            for card in p1_cards:
                player1.remove_card(card)
                player2.take_card(card)

    def __repr__(self):
        return 'SwapHands(target_id={})'.format(self._target_id)

    def __eq__(self, other):
        return isinstance(other, SwapHands) and self._target_id == other._target_id

    @property
    def help(self):
        return 'Swap hands with another player'

    @property
    def ready(self):
        return bool(self._target_id)


class ReplaceHand(InteractiveCommand):
    def __init__(self, cards=None, **kwargs):
        super().__init__(**kwargs)
        self._cards = cards or []

    def choices(self, player: Player, game: Game):
        cards = list(player.hand)
        for card in self._cards:
            cards.remove(card)
        return cards

    def select(self, choice):
        self._cards.append(choice)

    def apply(self, player: Player, game: Game):
        with EventTransaction(player, 'replaced_hand', player, len(self._cards)):
            for card in self._cards:
                player.remove_card(card)
                game.districts.put_on_bottom(card)
                player.take_card(game.districts.take_from_top())

    def __repr__(self):
        return 'ReplaceHand({})'.format(self._cards)

    def __eq__(self, other):
        return isinstance(other, ReplaceHand) and self._cards == other._cards

    @property
    def help(self):
        return 'Replace some cards'

    @property
    def ready(self):
        return bool(self._cards)


class Destroy(InteractiveCommand):
    def __init__(self, target_id=None, card=None, **kwargs):
        super().__init__(**kwargs)
        self._target_id = target_id
        self._card = card

    def _possible_districts(self, victim: Player, destroyer: Player):
        return [d for d in victim.city if rules.can_be_destroyed(d, victim) and rules.how_much_cost_to_destroy(d, destroyer) <= destroyer.gold]

    def choices(self, player: Player, game: Game):
        if not self._target_id:
            return [p.player_id for p in game.players if not rules.is_city_complete(p) and self._possible_districts(p, player)]  # WARLORD-SPARE-COMPLETE, WARLORD-DESTROY-OWN

        if not self._card:
            return self._possible_districts(game.players.find_by_id(self._target_id), player)

        return []

    def select(self, choice):
        if not self._target_id:
            self._target_id = choice
        elif not self._card:
            self._card = choice

    def apply(self, player: Player, game: Game):
        target = game.players.find_by_id(self._target_id)
        assert not rules.is_city_complete(target)
        target.destroy_district(self._card)
        cost = rules.how_much_cost_to_destroy(self._card, target)
        if cost > 0:
            player.withdraw(cost)
        game.districts.put_on_bottom(self._card)

    def __repr__(self):
        return 'Destroy(target_id={target_id}, card={card})'.format(target_id=self._target_id, card=self._card)

    def __eq__(self, other):
        return isinstance(other, Destroy) and (self._target_id, self._card) == (other._target_id, other._card)

    @property
    def help(self):
        return 'Destroy district'

    @property
    def ready(self):
        return self._target_id and self._card


class Build(InteractiveCommand):
    def __init__(self, district=None, **kwargs):
        super().__init__(**kwargs)
        self._district = district

    def apply(self, player: Player, game: Game):
        assert self._district
        with EventTransaction(player, 'district_built', player, self._district):
            cost = rules.how_much_cost_to_build(self._district, player)
            player.withdraw(cost)
            player.remove_card(self._district)
            player.build_district(self._district)

    def __repr__(self):
        return 'Build({})'.format(self._district)

    def __eq__(self, other):
        return isinstance(other, Build) and self._district == other._district

    def choices(self, player: Player, game: Game):
        if self._district:
            return []

        r = []
        for district in player.hand:
            if rules.can_be_built(district, player):
                if rules.how_much_cost_to_build(district, player) <= player.gold:
                    r.append(district)
        return r

    def select(self, choice):
        assert not self._district
        self._district = choice

    @property
    def help(self):
        return 'Build district'

    @property
    def ready(self):
        return self._district


class TakeCrown(Command):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def apply(self, player: Player, game: Game):
        assert player in game.players
        game.crowned_player = player

    def __repr__(self):
        return 'TakeCrown()'

    def __eq__(self, other):
        return isinstance(other, TakeCrown)

    @property
    def help(self):
        return 'Take crown'
