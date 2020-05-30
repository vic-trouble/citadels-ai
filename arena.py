from argparse import ArgumentParser
import multiprocessing

from ai.naive_bot import NaiveBotController
from ai.random_bot import RandomBotController
from citadels.cards import Deck, simple_districts, standard_chars
from citadels.game import Game
from citadels.gameplay import GameController
from citadels import rules


bots_spec = None


def play_some_games(num_games):
    try:
        game = Game(Deck(standard_chars()), Deck(simple_districts()))
        game_controller = GameController(game)

        bot_factory = {'R': RandomBotController, 'N': NaiveBotController}
        for i, b in enumerate(bots_spec):
            bot = game.add_player('Bot{}'.format(i + 1))
            game_controller.set_player_controller(bot, bot_factory[b]())

        scores = []
        winners = []
        for _ in range(num_games):
            while not game_controller.game_over:
                game_controller.play()

            scores.append([rules.score(player, game) for player in game.players])
            winners.append(game_controller.winner.player_id)

            game_controller.end_game()

        return scores, winners

    except KeyboardInterrupt:
        return None


def main():
    parser = ArgumentParser()
    parser.add_argument('--games', type=int, default=10000)
    parser.add_argument('--bots', type=str, default='NRR')
    args = parser.parse_args()

    global bots_spec
    bots_spec = args.bots
    num_games = args.games

    i = 0
    winrate = [0] * len(bots_spec)
    total_margin = 0

    def print_stats():
        total_winrate = sum(winrate) or 1
        data = {'games': i,
                'winrate': ' '.join('{:.2f}'.format(wr / total_winrate) for wr in winrate),
                'margin': total_margin / i}
        print('\r{games} games, win rate {winrate}, avg win score margin {margin:.1f}      '.format(**data), end='')

    pool = multiprocessing.Pool(8)
    try:
        while i < num_games:
            res = pool.map_async(play_some_games, [10]*8).get(999999999)
            if None in res:
                break
            for scores, winners in res:
                for score, winner in zip(scores, winners):
                    winrate[winner - 1] += 1
                    score = sorted(score, reverse=True)
                    margin = score[0] - score[1]
                    total_margin += margin

                    i += 1
                    if i % 10 == 0:
                        print_stats()

    except KeyboardInterrupt:
        print('\nCancelled by user')
    except RuntimeError as e:
        print(e)
    finally:
        if i:
            print_stats()
        print('Done')


if __name__ == '__main__':
    main()
