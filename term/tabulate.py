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
