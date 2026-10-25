"""Collects promo products from all stores into data/products.json.

Run: python scrape.py
"""
import json
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from scrapers import STORES
from scrapers.common import session

DATA_FILE = Path(__file__).parent / "data" / "products.json"


def _run(name, fn):
    started = time.time()
    try:
        items = [p for p in fn(session()) if p["name"]]
        return name, items, None, time.time() - started
    except Exception as e:  # one broken store must not stop the others
        traceback.print_exc()
        return name, [], f"{type(e).__name__}: {e}", time.time() - started


def load():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return None


def run_all():
    with ThreadPoolExecutor(len(STORES)) as pool:
        results = list(pool.map(lambda kv: _run(*kv), STORES.items()))

    old = load() or {"products": []}
    products, stores = [], {}
    for name, items, error, took in results:
        if error and not items:
            # keep the previous data of a store that failed this time
            items = [p for p in old["products"] if p["store"] == name]
        products += items
        stores[name] = {"count": len(items), "error": error, "seconds": round(took, 1)}

    data = {"updated": datetime.now().isoformat(timespec="seconds"),
            "stores": stores, "products": products}
    DATA_FILE.parent.mkdir(exist_ok=True)
    tmp = DATA_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    tmp.replace(DATA_FILE)
    return data


if __name__ == "__main__":
    data = run_all()
    for name, st in data["stores"].items():
        status = f"KLAIDA: {st['error']}" if st["error"] else "ok"
        print(f"{name:8} {st['count']:5} prekių  {st['seconds']:6}s  {status}")
    print(f"Iš viso: {len(data['products'])}  ->  {DATA_FILE}")
