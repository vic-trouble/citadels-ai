from term.io import assign_keys, emphasize, tabulate

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


def test_assign_keys_unique():
    assert assign_keys(['Take gold', 'Draw cards', 'Build district']) == ['t', 'd', 'b']


def test_assign_keys_repeating():
    assert assign_keys(['Draw cards', 'Draw sword']) == ['d', 'r']


def test_assign_keys_exhausted():
    assert assign_keys(['Try', 'Try', 'Try', 'Try']) == ['t', 'r', 'y', 'a']


def test_emphasize_upper():
    assert emphasize('Try', 't') == 'Try'


def test_emphasize_lower():
    assert emphasize('Try', 'r') == 'tRy'


def test_emphasize_missing():
    assert emphasize('Try', 'z') == 'Try'


def test_emphasize_two_words():
    assert emphasize('Try hits', 't') == 'Try hits'
