from term.io import tabulate

def test_empty():
    assert tabulate([]) == []


def test_single():
    assert tabulate(['single']) == ['single']


def test_many():
    assert tabulate(['one', 'two']) == ['one  two']


def test_custom_sep():
    assert tabulate(['one', 'two'], sep=' | ') == ['one | two']


def test_overflow():
    assert tabulate(['one', 'two'], width=3) == ['one', 'two']
