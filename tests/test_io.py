from colorama import Fore, Style
from term.io import assign_keys, emphasize, is_escape_code, join_text, lex, strip_coloring, tabulate

def test_tabulate_empty():
    assert tabulate([]) == []


def test_tabulate_single():
    assert tabulate(['single']) == ['single']


def test_tabulate_many():
    assert tabulate(['one', 'two']) == ['one  two']


def test_tabulate_custom_sep():
    assert tabulate(['one', 'two'], sep=' | ') == ['one | two']


def test_tabulate_overflow():
    assert tabulate(['one', 'two'], width=3) == ['one', 'two']


def test_tabulate_2x2():
    assert tabulate(['one', 'two', 'three', 'four'], width=15) == ['one    two  ', 'three  four ']


def test_tabulate_2x2_colored():
    assert tabulate([f'{Fore.GREEN}one{Style.RESET_ALL}', 'two', 'three', 'four'], width=15) == [f'{Fore.GREEN}one{Style.RESET_ALL}    two  ', 'three  four ']


def test_assign_keys_unique():
    assert assign_keys(['Take gold', 'Draw cards', 'Build district']) == ['t', 'd', 'b']


def test_assign_keys_repeating():
    assert assign_keys(['Draw cards', 'Draw sword']) == ['d', 'r']


def test_assign_keys_exhausted():
    assert assign_keys(['Try', 'Try', 'Try', 'Try']) == ['t', 'r', 'y', 'a']


def test_assign_keys_ignores_coloring():
    assert assign_keys([f'{Fore.GREEN}Green{Style.RESET_ALL}']) == ['g']


def test_strip_coloring():
    assert strip_coloring(f'Some {Fore.GREEN}green{Style.RESET_ALL} text') == 'Some green text'


def test_emphasize_upper():
    assert emphasize('Try', 't') == 'Try'


def test_emphasize_lower():
    assert emphasize('Try', 'r') == 'tRy'


def test_emphasize_missing():
    assert emphasize('Try', 'z') == 'Try'


def test_emphasize_two_words():
    assert emphasize('Try hits', 't') == 'Try hits'


def test_emphasize_coloring_m():
    assert emphasize(f'{Fore.GREEN}merchant', 'm') == f'{Fore.GREEN}Merchant'


def test_emphasize_with_numbers():
    assert emphasize('Take 2 cards', 't') == 'Take 2 cards'


def test_lex():
    text = f'Quick {Fore.RED}fox{Style.RESET_ALL} jumped over a lazy dog!'
    lexems = ['Quick', Fore.RED, 'fox', Style.RESET_ALL, 'jumped', 'over', 'a', 'lazy', 'dog', '!']
    assert list(lex(text)) == lexems


def test_lex_punctuation():
    text = 'Take 2 cards (1 to keep, sure)'
    lexems = ['Take', '2', 'cards', '(', '1', 'to', 'keep', ',', 'sure', ')']
    assert list(lex(text)) == lexems


def test_join_text():
    lexems = ['Quick', Fore.RED, 'fox', Style.RESET_ALL, 'jumped', 'over', 'a', 'lazy', 'dog', '!']
    text = f'Quick{Fore.RED} fox{Style.RESET_ALL} jumped over a lazy dog!'
    assert join_text(lexems) == text


def test_join_text_with_punctuation():
    lexems = ['Take', '2', 'cards', '(', '1', 'to', 'keep', ',', 'sure', ')']
    text = 'Take 2 cards (1 to keep, sure)'
    assert join_text(lexems) == text


def test_is_escape_code():
    assert not is_escape_code('King')
    assert is_escape_code(Fore.RED)
    assert is_escape_code(Style.RESET_ALL)
