__author__ = 'skeggsc'

import world


def load(filename, tileset, time_provider):
    with open(filename, "r") as f:
        refs = {}
        types = {}
        solid = []
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line == "%%":
                break
            symbol, ref, *args = line.split(" ")
            if symbol == "solid":
                solid += [tuple(int(k) for k in x.split(",")) for x in [ref] + args]
                assert all(len(x) == 2 for x in solid)
                continue
            assert len(symbol) == 1, "for now, symbols must be one character long"
            assert symbol not in types, "multiple definitions for symbol: '%s'" % symbol
            if ref not in refs:
                base, attr = ref.split(".")
                refs[ref] = getattr(__import__(base), attr)
            pargs = [int(arg) if arg.isdigit() else arg for arg in args]
            types[symbol] = (refs[ref], pargs)
        else:
            raise Exception("Did not find proper end of map!")
        assert solid
        # map body
        rows = []
        for row in f:
            row = row.strip('\n')
            if rows:
                assert len(rows[0]) == len(row), "mismatched row lengths"
            rows.append([types[c][0](*types[c][1]) for c in row])
        assert rows, "map cannot be empty!"
        columns = tuple(zip(*rows))
    return world.World(columns, tileset, solid, time_provider)
