"""Akcijų paieška: python app.py  ->  http://127.0.0.1:5000"""
import re
import threading
import unicodedata

from flask import Flask, jsonify, request, send_from_directory

import scrape

app = Flask(__name__, static_folder="static")

_lock = threading.Lock()
_state = {"data": None, "index": [], "refreshing": False, "error": None}


# Lithuanian endings (without diacritics), longest first, so "kava" also finds "kavos"
ENDINGS = ("iais", "iai", "ams", "oms", "ems", "ius", "iu", "io", "as", "is", "ys", "us",
           "os", "es", "ai", "ei", "ui", "a", "e", "i", "o", "u", "y")


def norm(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def term_pattern(term):
    if term.isalpha():
        for e in ENDINGS:
            if term.endswith(e) and len(term) - len(e) >= 3:
                term = term[:-len(e)]
                break
    # match from the start of a word: "kava" must not hit "kakava"
    return re.compile(r"(?<![a-z0-9])" + re.escape(term))


def unit_price(p):
    return p["price"] / p["qty"] if p["price"] else None


def _set_data(data):
    index = [(norm(f"{p['name']} {p['details']}"), p) for p in data["products"]]
    with _lock:
        _state["data"], _state["index"] = data, index


def _refresh():
    try:
        _set_data(scrape.run_all())
        _state["error"] = None
    except Exception as e:
        _state["error"] = str(e)
    finally:
        _state["refreshing"] = False


def start_refresh():
    with _lock:
        if _state["refreshing"]:
            return False
        _state["refreshing"] = True
    threading.Thread(target=_refresh, daemon=True).start()
    return True


SORTS = {
    "price": lambda p: (unit_price(p) is None, unit_price(p) or 0),
    "discount": lambda p: (p["discount"] is None, -(p["discount"] or 0)),
    "name": lambda p: norm(p["name"]),
}


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/status")
def status():
    data = _state["data"] or {}
    return jsonify(updated=data.get("updated"), stores=data.get("stores", {}),
                   total=len(data.get("products", [])),
                   refreshing=_state["refreshing"], error=_state["error"])


@app.post("/api/refresh")
def refresh():
    return jsonify(started=start_refresh())


@app.get("/api/search")
def search():
    terms = [term_pattern(t) for t in norm(request.args.get("q", "")).split()]
    stores = set(filter(None, request.args.get("stores", "").split(",")))
    no_card = request.args.get("no_card") == "1"
    only_priced = request.args.get("priced") == "1"
    sort = request.args.get("sort") or ("price" if terms else "discount")
    offset = max(int(request.args.get("offset", 0)), 0)
    limit = min(max(int(request.args.get("limit", 60)), 1), 200)

    with _lock:
        index = _state["index"]
    hits = [p for text, p in index
            if all(t.search(text) for t in terms)
            and (not stores or p["store"] in stores)
            and not (no_card and p["card"])
            and not (only_priced and not p["price"])]
    hits.sort(key=SORTS.get(sort, SORTS["price"]))

    cheapest = {}
    for p in hits:
        u = unit_price(p)
        if u is not None and (p["store"] not in cheapest or u < cheapest[p["store"]]["unit"]):
            cheapest[p["store"]] = {"unit": round(u, 2), "name": p["name"]}

    return jsonify(total=len(hits), offset=offset, items=hits[offset:offset + limit],
                   cheapest=dict(sorted(cheapest.items(), key=lambda kv: kv[1]["unit"])))


def main():
    data = scrape.load()
    if data:
        _set_data(data)
    else:
        start_refresh()
    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    main()
