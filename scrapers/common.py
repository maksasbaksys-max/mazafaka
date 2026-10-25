import re

import requests

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)


def session():
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept-Language": "lt-LT,lt;q=0.9"})
    return s


def text(el):
    return " ".join(el.get_text(" ", strip=True).split()) if el else ""


def money(s):
    """'2,49 €' / 'Įprasta kaina: 0.85€' -> 2.49"""
    if not s:
        return None
    m = re.search(r"(\d+)[.,](\d{1,2})", s)
    if m:
        return float(f"{m.group(1)}.{m.group(2).ljust(2, '0')}")
    m = re.search(r"\d+", s)
    return float(m.group()) if m else None


def euro(integer, cents):
    """Price split into separate integer / cents elements."""
    i, c = text(integer), text(cents)
    if not i.isdigit():
        return None
    c = re.sub(r"\D", "", c) or "0"
    return float(f"{i}.{c.ljust(2, '0')[:2]}")


def bundle_qty(deal):
    """'2 vnt. už' / 'Įsidėk 3 už' -> 2 / 3: the price shown is for that many items."""
    m = re.search(r"(\d+)\s*(?:vnt\.?\s*)?už", deal or "", re.I)
    return int(m.group(1)) if m else 1


def product(store, name, price=None, old_price=None, image="", url="", deal="",
            card=False, unit_price="", details="", valid="", qty=1, image_fallback=""):
    discount = None
    if price and old_price:
        unit = price / qty
        if old_price > unit:
            discount = round((1 - unit / old_price) * 100)
    return {
        "store": store,
        "name": name,
        "image": image,
        "image_fallback": image_fallback,  # used by the page when `image` fails to load
        "url": url,
        "price": price,
        "old_price": old_price if discount is not None else None,
        "discount": discount,
        "qty": qty,
        "deal": deal,
        "card": card,
        "unit_price": unit_price,
        "details": details,
        "valid": valid,
    }
