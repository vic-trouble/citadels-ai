from citadels.cards import Character, District, all_chars
from citadels.game import Game, Player
from citadels import rules


class Command:
    def apply(self, player: Player, game: Game):
        raise NotImplementedError()


class InteractiveCommand(Command):
    def choices(self, player: Player, game: Game):
        raise NotImplementedError()

    def select(self, choice):
        raise NotImplementedError()

    # TODO: add restart()


class CashIn(Command):
    def __init__(self, amount):
        self._amount = amount

    def apply(self, player: Player, game: Game):
        player.cash_in(self._amount)


class DrawCards(Command):
    def __init__(self, draw=2, keep=1):
        self._draw = draw
        self._keep = keep  # TODO: not implemented :(

    def apply(self, player: Player, game: Game):
        for _ in range(self._draw):
            player.hand.append(game.districts.take_from_top())


class Kill(InteractiveCommand):
    def __init__(self):
        self._char = None

    def choices(self, player: Player, game: Game):
        return [char for char in all_chars if char != Character.Assassin] if not self._char else []

    def select(self, choice):
        self._char = choice

    def apply(self, player: Player, game: Game):
        assert self._char
        assert not game.turn.killed_char
        game.turn.killed_char = self._char


class Rob(InteractiveCommand):
    def __init__(self):
        self._char = None

    def choices(self, player: Player, game: Game):
        return [char for char in all_chars if char not in (Character.Assassin, game.turn.killed_char)] if not self._char else []

    def select(self, choice):
        self._char = choice

    def apply(self, player: Player, game: Game):
        assert self._char
        assert not game.turn.robbed_char
        game.turn.robbed_char = self._char


class SwapHands(InteractiveCommand):
    def __init__(self):
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


class ReplaceHand(InteractiveCommand):
    def __init__(self):
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


class Destroy(InteractiveCommand):
    def __init__(self):
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


class Build(Command):
    def __init__(self, district: District):
        self._district = district

    def apply(self, player: Player, game: Game):
        cost = rules.how_much_cost_to_build(self._district, player)
        player.withdraw(cost)
        player.hand.remove(self._district)
        player.city.append(self._district)
