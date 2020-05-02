from enum import IntFlag, auto

from citadels.cards import Character, District, all_chars
from citadels.game import Game, Player
from citadels import rules


class Restriction(IntFlag):
    OnStartTurn = auto()
    OnEndTurn = auto()
    OnAfterAction = auto()
    Compulsory = auto()


class Command:
    def __init__(self, restriction=None):
        self.restriction=restriction

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

    @property
    def help(self):
        raise NotImplementedError()

    # TODO: add restart()


class CashIn(Command):
    def __init__(self, amount, **kwargs):
        super().__init__(**kwargs)
        self._amount = amount

    def apply(self, player: Player, game: Game):
        player.cash_in(self._amount)

    def __repr__(self):
        return 'CashIn({})'.format(self._amount)

    def __eq__(self, other):
        return isinstance(other, CashIn) and self._amount == other._amount


class DrawCards(Command):
    def __init__(self, draw=2, keep=1, **kwargs):
        super().__init__(**kwargs)
        self._draw = draw
        self._keep = keep  # TODO: not implemented :(

    def apply(self, player: Player, game: Game):
        for _ in range(self._draw):
            player.hand.append(game.districts.take_from_top())

    def __repr__(self):
        return 'DrawCards(draw={draw}, keep={keep})'.format(draw=self._draw, keep=self._keep)

    def __eq__(self, other):
        return isinstance(other, DrawCards) and (self._draw, self._keep) == (other._draw, other._keep)


class Kill(InteractiveCommand):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._char = None

    def choices(self, player: Player, game: Game):
        return [char for char in all_chars if char != Character.Assassin] if not self._char else []

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


class Rob(InteractiveCommand):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._char = None

    def choices(self, player: Player, game: Game):
        return [char for char in all_chars if char not in (Character.Assassin, game.turn.killed_char)] if not self._char else []

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


class SwapHands(InteractiveCommand):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._target = None

    def choices(self, player: Player, game: Game):
        return [p for p in game.players if p.player_id != player.player_id] if not self._target else []

    def select(self, choice):
        self._target = choice

    def apply(self, player: Player, game: Game):
        assert self._target
        player1 = game.players.find_by_id(player.player_id)
        player2 = game.players.find_by_id(self._target.player_id)
        player1.hand, player2.hand = player2.hand, player1.hand

    def __repr__(self):
        return 'SwapHands({})'.format(self._target)

    def __eq__(self, other):
        return isinstance(other, SwapHands) and self._target == other._target


class ReplaceHand(InteractiveCommand):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._cards = []

    def choices(self, player: Player, game: Game):
        return [card for card in player.hand if card not in self._cards]

    def select(self, choice):
        self._cards.append(choice)

    def apply(self, player: Player, game: Game):
        for card in self._cards:
            player.hand.remove(card)
            game.districts.put_on_bottom(card)
            player.hand.append(game.districts.take_from_top())

    def __repr__(self):
        return 'ReplaceHand({})'.format(self._cards)

    def __eq__(self, other):
        return isinstance(other, ReplaceHand) and self._cards == other._cards


class Destroy(InteractiveCommand):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._target = None
        self._card = None

    def choices(self, player: Player, game: Game):
        if not self._target:
            return [p for p in game.players if not rules.is_city_complete(p)] # WARLORD-SPARE-COMPLETE, WARLORD-DESTROY-OWN

        if not self._card:
            victim = game.players.find_by_id(self._target.player_id)
            return [district for district in victim.city if rules.can_be_destroyed(district, victim)]

        return []

    def select(self, choice):
        if not self._target:
            self._target = choice
        elif not self._card:
            self._card = choice

    def apply(self, player: Player, game: Game):
        target = game.players.find_by_id(self._target.player_id)
        assert not rules.is_city_complete(target)
        target.city.remove(self._card)

    def __repr__(self):
        return 'Destroy(target={target}, card={card})'.format(target=self._target, card=self._card)

    def __eq__(self, other):
        return isinstance(other, Destroy) and (self._target, self._card) == (other._target, other._card)


class Build(InteractiveCommand):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._district = None

    def apply(self, player: Player, game: Game):
        cost = rules.how_much_cost_to_build(self._district, player)
        player.withdraw(cost)
        player.hand.remove(self._district)
        player.city.append(self._district)

    def __repr__(self):
        return 'Build({})'.format(self._district)

    def __eq__(self, other):
        return isinstance(other, Build) and self._district == other._district

    def choices(self, player: Player, game: Game):
        r = []
        for district in player.hand:
            if rules.can_be_built(district, player):
                if rules.how_much_cost_to_build(district, player) <= player.gold:
                    r.append(district)
        return r

    def select(self, choice):
        assert not self._district
        self._district = choice


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
