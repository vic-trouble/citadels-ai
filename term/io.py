from itertools import chain
import string


def tabulate(entries, sep='  ', width=80):
    entries = list(entries)

    if not entries:
        return []

    def pad(s: str, width: int):
        return s + ' ' * max(width - len(s), 0)

    def chunk(iterable, length):
        ch = []
        for i in iterable:
            ch.append(i)
            if len(ch) == length:
                yield ch
                ch = []
        if ch:
            yield ch

    max_length = max(len(e) for e in entries)
    entries_per_line = width // max_length
    if entries_per_line == 0:
        entries_per_line = 1
    elif entries_per_line * max_length + (entries_per_line - 1) * len(sep) > width:
        entries_per_line -= 1

    r = []
    for ch in chunk(entries, entries_per_line):
        r.append(sep.join(pad(s, max_length) for s in ch))
    return r


def dialog(prolog: str, choices=None, help=None, allow_empty=False):
    def is_iterable(obj):
        try:
            iter(obj)
            return True
        except TypeError:
            return False

    while True:
        if help:
            print(prolog)
            print('\n'.join(tabulate('{k}: {v}'.format(k=k, v=v) for k, v in help.items())))
            print('> ', end='')
        else:
            print(prolog + ': ', end='')
        inp = input()
        if not inp:
            if allow_empty:
                return ''
            else:
                continue
        if not choices:
            return inp
        if is_iterable(choices):
            if inp in choices:
                return inp
        elif callable(choices):
            if choices(inp):
                return inp
        else:
            raise TypeError('Invalid choices')


def assign_keys(choices):
    res = ['?'] * len(choices)
    all_marks = tuple(chain(string.ascii_lowercase, string.ascii_uppercase, string.digits))
    choices = list(enumerate(choices))
    orig_choices = list(choices)
    choices_update = list(choices)
    j = 0
    while choices:
        for i, choice in choices:
            if j < len(choice):
                mark = choice[j].lower()
            else:
                mark = next(iter(mark for mark in all_marks if mark not in res))
            if mark not in res:
                res[i] = mark
                choices_update.remove((i, choice))
        j += 1
        choices = choices_update
    return res


def emphasize(word, letter):
    if letter in word.lower():
        word = word.lower()
        i = word.index(letter)
        return word[:i] + letter.upper() + word[i+1:]
    return word
