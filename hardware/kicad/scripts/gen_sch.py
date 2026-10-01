"""Genera EyeNode.kicad_sch dalle definizioni in eyenode_design.py.
Connessioni tramite etichette di rete sui terminali dei pin (niente fili)."""
import json
import uuid
from pathlib import Path

from sexp import Sym, dump, find, find1, parse
import eyenode_design as D

LIBDIR = Path(r"C:/Program Files/KiCad/10.0/share/kicad/symbols")
OUT = Path(__file__).resolve().parents[1] / D.PROJECT
OUT.mkdir(parents=True, exist_ok=True)
NS = uuid.UUID("6f1c2a52-0d0e-4d55-9a70-1d7a1e0c0de5")
ROOT_UUID = str(uuid.uuid5(NS, "root"))
_libcache = {}


def U(*k):
    return str(uuid.uuid5(NS, "/".join(map(str, k))))


def lib_symbol(lib_id):
    lib, name = lib_id.split(":")
    if lib not in _libcache:
        t = parse((LIBDIR / f"{lib}.kicad_sym").read_text(encoding="utf8"))
        _libcache[lib] = {x[1]: x for x in find(t, "symbol")}
    syms = _libcache[lib]
    s = syms[name]
    ext = find1(s, "extends")
    if not ext:
        out = [Sym("symbol"), lib_id] + [x for x in s[2:]]
        return _rename_units(out, name, name)
    parent = lib_symbol(f"{lib}:{ext[1]}")
    props = {p[1]: p for p in find(s, "property")}
    out = [Sym("symbol"), lib_id]
    for x in parent[2:]:
        if isinstance(x, list) and x and x[0] == "property" and x[1] in props:
            out.append(props.pop(x[1]))
        else:
            out.append(x)
    out[2:2] = list(props.values())
    return _rename_units(out, ext[1], name)


def _rename_units(sym, old, new):
    res = []
    for x in sym:
        if isinstance(x, list) and x and x[0] == "symbol":
            x = [x[0], x[1].replace(old + "_", new + "_", 1)] + x[2:]
        res.append(x)
    return res


def pins_of(sym):
    out = []

    def walk(e):
        for x in e:
            if isinstance(x, list):
                if x and x[0] == "pin":
                    at = find1(x, "at")
                    out.append(dict(num=find1(x, "number")[1], name=find1(x, "name")[1],
                                    type=str(x[1]), x=float(at[1]), y=float(at[2]), a=int(float(at[3]))))
                walk(x)
    walk(sym)
    return out


def resolve(pins, key):
    for p in pins:
        if p["num"] == key:
            return [p]
    r = [p for p in pins if p["name"] == key]
    if not r:
        raise KeyError(key)
    return r


def prop(name, value, x, y, hide=False):
    e = [Sym("property"), name, value, [Sym("at"), x, y, 0],
         [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]]] + ([[Sym("hide"), Sym("yes")]] if hide else [])]
    return e


def sym_instance(ref, lib_id, value, fp, x, y, pins, extra_props=(), rot=0):
    e = [Sym("symbol"), [Sym("lib_id"), lib_id], [Sym("at"), x, y, rot], [Sym("unit"), 1],
         [Sym("exclude_from_sim"), Sym("no")], [Sym("in_bom"), Sym("no" if ref.startswith(("#", "H")) else "yes")],
         [Sym("on_board"), Sym("no" if ref.startswith("#") else "yes")], [Sym("dnp"), Sym("no")],
         [Sym("uuid"), U("sym", ref)],
         prop("Reference", ref, x, y - 6, hide=ref.startswith("#")),
         prop("Value", value, x, y + 6),
         prop("Footprint", fp, x, y, hide=True),
         prop("Datasheet", "", x, y, hide=True)]
    e += list(extra_props)
    for p in {p["num"] for p in pins}:
        e.append([Sym("pin"), p, [Sym("uuid"), U("pin", ref, p)]])
    e.append([Sym("instances"), [Sym("project"), D.PROJECT,
              [Sym("path"), "/" + ROOT_UUID, [Sym("reference"), ref], [Sym("unit"), 1]]]])
    return e


def label(net, x, y, a, key):
    just = {0: "left", 90: "left", 180: "right", 270: "right"}[a]
    return [Sym("label"), net, [Sym("at"), round(x, 2), round(y, 2), a],
            [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]], [Sym("justify"), Sym(just), Sym("bottom")]],
            [Sym("uuid"), U("lbl", key)]]


def build():
    libs, items, netmap = {}, [], {}
    for c in D.parts:
        s = lib_symbol(c["lib"])
        if c["lib"] == "MCU_Module:Arduino_Nano_v3.x":
            # il +5V del Nano viene alimentato dall'R-78: lo trattiamo come ingresso
            def fix(e):
                for x in e:
                    if isinstance(x, list):
                        if x and x[0] == "pin" and find1(x, "name")[1] == "+5V":
                            x[1] = Sym("power_in")
                        fix(x)
            fix(s)
        libs[c["lib"]] = s
        pins = pins_of(s)
        X, Y = c["sch"][:2]
        rot = c["sch"][2] if len(c["sch"]) > 2 else 0
        items.append(sym_instance(c["ref"], c["lib"], c["value"], c["fp"], X, Y, pins,
                                  [prop("Description", c.get("desc", ""), X, Y, hide=True)], rot))
        used = set()
        for key, net in c["pins"].items():
            for p in resolve(pins, key):
                used.add(p["num"])
                import math
                ca, sa = round(math.cos(math.radians(rot))), round(math.sin(math.radians(rot)))
                rx, ry = p["x"] * ca - p["y"] * sa, p["x"] * sa + p["y"] * ca
                px, py = X + rx, Y - ry
                if net is None:
                    items.append([Sym("no_connect"), [Sym("at"), round(px, 2), round(py, 2)],
                                  [Sym("uuid"), U("nc", c["ref"], p["num"])]])
                else:
                    items.append(label(net, px, py, (p["a"] + rot + 180) % 360, f"{c['ref']}.{p['num']}"))
                    netmap.setdefault(net, []).append(f"{c['ref']}.{p['num']}")
        missing = {p["num"] for p in pins} - used
        if missing:
            raise SystemExit(f"{c['ref']}: pin non assegnati {sorted(missing)}")

    flag = lib_symbol("power:PWR_FLAG")
    libs["power:PWR_FLAG"] = flag
    for ref, net, (x, y) in D.FLAGS:
        items.append(sym_instance(ref, "power:PWR_FLAG", "PWR_FLAG", "", x, y, pins_of(flag)))
        items.append(label(net, x, y, 270, ref))

    hole = lib_symbol("Mechanical:MountingHole")
    libs["Mechanical:MountingHole"] = hole
    for i, (ref, _) in enumerate(D.HOLES):
        items.append(sym_instance(ref, "Mechanical:MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3",
                                  30.48 + i * 12.7, 180.34, []))

    for i, (txt, x, y) in enumerate(getattr(D, "NOTES", [])):
        items.append([Sym("text"), txt, [Sym("exclude_from_sim"), Sym("no")], [Sym("at"), x, y, 0],
                      [Sym("effects"), [Sym("font"), [Sym("size"), 2.0, 2.0], [Sym("bold"), Sym("yes")]],
                       [Sym("justify"), Sym("left"), Sym("bottom")]], [Sym("uuid"), U("txt", i)]])
    title = [Sym("title_block"), [Sym("title"), "EyeNode - controllo coppia occhi animatronici"],
             [Sym("company"), "Idra di Guerra - Carnevale di Viareggio"], [Sym("rev"), "0.1"],
             [Sym("comment"), 1, "6 servo MG90S, RS-485, Arduino Nano"]]
    sch = [Sym("kicad_sch"), [Sym("version"), 20250114], [Sym("generator"), "eeschema"],
           [Sym("generator_version"), "9.0"], [Sym("uuid"), ROOT_UUID], [Sym("paper"), "A3"], title,
           [Sym("lib_symbols")] + list(libs.values())] + items + \
          [[Sym("sheet_instances"), [Sym("path"), "/", [Sym("page"), "1"]]], [Sym("embedded_fonts"), Sym("no")]]
    (OUT / f"{D.PROJECT}.kicad_sch").write_text(dump(sch) + "\n", encoding="utf8")
    (OUT / "netmap.json").write_text(json.dumps(netmap, indent=1), encoding="utf8")
    print("nets:", len(netmap), " parts:", len(D.parts))


if __name__ == "__main__":
    build()
