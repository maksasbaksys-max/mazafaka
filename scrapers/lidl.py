import json
from datetime import datetime

from bs4 import BeautifulSoup

from .common import product

BASE = "https://www.lidl.lt"
URL = BASE + "/c/svarbiausios-sios-savaites-akcijos/a10023711"


def _date(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).strftime("%m.%d")
    except (AttributeError, ValueError):
        return ""


def _offers(d):
    """(price block, needs Lidl Plus) pairs; regionsPrices carries the complete data."""
    region = (d.get("regionsPrices") or {}).get("1") or {}
    found = []
    if (region.get("currentPrice") or {}).get("price"):
        found.append((region["currentPrice"], False))
    plus = (region.get("currentLidlPlusPrice") or {}).get("price") or {}
    if plus.get("price"):
        found.append((plus, True))
    if not found:
        if (d.get("price") or {}).get("price"):
            found.append((d["price"], False))
        for lp in d.get("lidlPlus") or []:
            if (lp.get("price") or {}).get("price"):
                found.append((lp["price"], True))
    return found


def parse_item(d):
    offers = _offers(d)
    if offers:
        block, plus = min(offers, key=lambda o: o[0]["price"])
        discount = block.get("discount") or {}
        price = block["price"]
        old = discount.get("deletedPrice") or block.get("oldPrice")
        deal = discount.get("discountText", "") if discount.get("showDiscount") else ""
        unit = (block.get("basePrice") or {}).get("text", "")
        size = (block.get("packaging") or {}).get("text", "")
        start, end = _date(block.get("startDate")), _date(block.get("endDate"))
    else:
        price = old = None
        plus, deal, unit, size, start, end = False, "", "", "", "", ""
    return product(
        "Lidl",
        d.get("fullTitle") or d.get("title", ""),
        price=price,
        old_price=old,
        image=d.get("image", ""),
        url=BASE + d.get("canonicalUrl", ""),
        deal=deal,
        card=plus,
        unit_price=unit,
        details=size,
        valid=f"{start} - {end}" if start and end else "",
    )


def scrape(s):
    soup = BeautifulSoup(s.get(URL, timeout=30).text, "html.parser")
    out, seen = [], set()
    for el in soup.select("[data-grid-data]"):
        try:
            d = json.loads(el["data-grid-data"])
        except ValueError:
            continue
        pid = d.get("productId")
        if pid in seen or not d.get("fullTitle"):
            continue
        seen.add(pid)
        out.append(parse_item(d))
    return out
