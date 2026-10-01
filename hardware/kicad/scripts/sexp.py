"""Mini parser/serializer S-expression per file KiCad."""
import re

_tok = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))', re.S)
BS = chr(92)  # backslash


class Sym(str):
    """Atomo non quotato."""


def _unescape(s):
    return s.replace(BS + '"', '"').replace(BS + BS, BS)


def parse(text):
    stack, cur = [], []
    for m in _tok.finditer(text):
        lp, rp, qs, at = m.groups()
        if lp:
            stack.append(cur)
            cur = []
        elif rp:
            done = cur
            cur = stack.pop()
            cur.append(done)
        elif qs is not None:
            cur.append(_unescape(qs))
        elif at is not None:
            cur.append(Sym(at))
    return cur[0] if len(cur) == 1 else cur


def dump(e, ind=0):
    if isinstance(e, list):
        if not e:
            return "()"
        if all(not isinstance(x, list) for x in e):
            return "(" + " ".join(dump(x) for x in e) + ")"
        out = "(" + " ".join(dump(x) for x in e if not isinstance(x, list))
        for x in e:
            if isinstance(x, list):
                out += "\n" + "\t" * (ind + 1) + dump(x, ind + 1)
        return out + "\n" + "\t" * ind + ")"
    if isinstance(e, Sym):
        return str(e)
    if isinstance(e, bool):
        return "yes" if e else "no"
    if isinstance(e, float):
        return f"{e:.4f}".rstrip("0").rstrip(".")
    if isinstance(e, int):
        return str(e)
    s = str(e).replace(BS, BS + BS).replace('"', BS + '"')
    return f'"{s}"'


def find(e, key):
    return [x for x in e if isinstance(x, list) and x and x[0] == key]


def find1(e, key):
    r = find(e, key)
    return r[0] if r else None
