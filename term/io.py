from itertools import chain
import string


def tabulate(entries, sep='  ', width=80):
    entries = list(entries)

    if not entries:
        return []

    def pad(s: str, width: int):
        return s + ' ' * max(width - len(strip_coloring(s)), 0)

    def chunk(iterable, length):
        ch = []
        for i in iterable:
            ch.append(i)
            if len(ch) == length:
                yield ch
                ch = []
        if ch:
            yield ch

    max_length = max(len(strip_coloring(e)) for e in entries)
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


def strip_coloring(text):
    return join_text(lexem for lexem in lex(text) if not is_escape_code(lexem))


def assign_keys(choices):
    res = ['?'] * len(choices)
    all_marks = tuple(chain(string.ascii_lowercase, string.ascii_uppercase, string.digits))
    choices = list(enumerate(strip_coloring(choice) for choice in choices))
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


def emphasize(text: str, letter: str):
    if letter not in strip_coloring(text).lower():
        return text

    r = []
    for lexem in lex(text):
        if is_escape_code(lexem):
            r.append(lexem)
        else:
            rw = []
            for c in lexem.lower():
                if c == letter:
                    rw.append(c.upper())
                    letter = None
                else:
                    rw.append(c)
            r.append(''.join(rw))

    return join_text(r)


def is_punctuation(c):
    return c in ',.?!;:()'

def lex(text):
    cur = ''
    word = set(chain(string.ascii_lowercase, string.ascii_uppercase, string.digits, '_'))

    for c in text + '\0':
        if is_escape_code(cur): # simplified escape code parsing
            cur += c
            if cur[1] != '[':
                yield cur
                cur = ''
            elif c == 'm':
                yield cur
                cur = ''
            continue

        if c.isspace():
            if cur:
                yield cur
                cur = ''
        elif c in word:
            cur = cur + c
        elif is_escape_code(c):
            if cur:
                yield cur
            cur = c
        elif is_punctuation(c):
            if cur:
                yield cur
                cur = ''
            yield c
        else:
            if cur:
                yield cur
            cur = c


def is_escape_code(text):
    return text.startswith('\x1b')


def join_text(lexems):
    r = []
    word = set(chain(string.ascii_lowercase, string.ascii_uppercase, string.digits, '_'))
    for lexem in lexems:
        if r and (lexem[0] in word or is_punctuation(lexem)) and any(not is_escape_code(prev) for prev in r):
            r.append(' ')
        r.append(lexem)

    # fix punctuation
    s = ''.join(r)
    for punct, fix in [('( ', '('), (' )', ')'), (' ,', ','), (' .', ','), (' !', '!'), (' ?', '?')]:
        s = s.replace(punct, fix)
    return s
