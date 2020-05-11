from collections import defaultdict

from ai.bot import BotController
from citadels.cards import Deck, simple_districts, standard_chars
from citadels.game import Game
from citadels.gameplay import GameController
from citadels import rules


def main():
    game = Game(Deck(standard_chars()), Deck(simple_districts()))
    game_controller = GameController(game)

    num_games = 10000

    num_players = 4
    for i in range(num_players):
        bot = game.add_player('Bot{}'.format(i))
        game_controller.set_player_controller(bot, BotController())

    winrate = [0] * num_players
    total_margin = 0

    def print_stats():
        total_winrate = sum(winrate) or 1
        data = {'games': i,
                'winrate': ' '.join('{:.2f}'.format(wr / total_winrate) for wr in winrate),
                'margin': total_margin / i}
        print('\r{games} games, win rate {winrate}, avg win score margin {margin:.1f}      '.format(**data), end='')

    try:
        for i in range(1, num_games+1):
            while not game_controller.game_over:
                game_controller.play()
            winrate[game_controller.winner.player_id - 1] += 1

            score = sorted((rules.score(player, game) for player in game.players), reverse=True)
            margin = score[0] - score[1]
            total_margin += margin

            if i % 10 == 0:
                print_stats()

            game_controller.end_game()

    except RuntimeError as e:
        print(e)
    finally:
        print_stats()


if __name__ == '__main__':
    main()
