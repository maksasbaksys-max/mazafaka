import re
import time

from bs4 import BeautifulSoup

from .common import euro, product, text

URL = "https://iki.lt/akcijos/savaites-akcijos/"
API = "https://iki.lt/wp-json/promos/web-promos"
TAG = 9  # "Savaitės akcijos"
MAX_PAGES = 200


def parse_item(p):
    promo = p.select_one(".promo_price")
    link = p.select_one("a[href]")
    img = p.select_one("img")
    price = old = None
    qty = 1
    deal = ""
    if promo:
        deal = text(promo.select_one(".price_block_red_wrapper")).replace(" ", "")
        box = promo.select_one(".price_block_wrapper")
        if box:
            price = euro(box.find(class_="price_int", recursive=False),
                         box.select_one(".price_cents .sub"))
            old_box = box.select_one(".price_old_block")
            if old_box:
                old = euro(old_box.select_one(".price_int"), old_box.select_one(".price_cents"))
                if "SUTAUPOTE" in text(box).upper() and price and old:
                    # "2+1 1,58 € SUTAUPOTE 0,79 €": the shown amounts are for the whole set
                    m = re.match(r"(\d+)\+(\d+)", deal)
                    qty = int(m.group(1)) + int(m.group(2)) if m else 1
                    old = round((price + old) / qty, 2)
        if deal in ("TIK", "SUPERKAINA"):
            deal = "SUPER KAINA" if deal == "SUPERKAINA" else ""
    paras = [text(x) for x in p.select("p")]
    valid = next((x for x in paras if x.lower().startswith("galioja")), "")
    details = next((x for x in paras if x and x != valid and "kaina" not in x.lower()
                    and x.upper() != "SUTAUPOTE"), "")
    unit = re.search(r"[\d,]+\s*Eur/\w+", details)
    image = img.get("src", "") if img else ""
    # "_large.jpg" is often 2+ MB; the plain ".jpg" is ~10x smaller but not always present
    small = image.replace("_large.jpg", ".jpg") if image.endswith("_large.jpg") else ""
    return product(
        "IKI",
        text(p.select_one("h2")),
        price=price,
        old_price=old,
        image=small or image,
        image_fallback=image if small else "",
        url=link["href"] if link else URL,
        deal=deal,
        card=bool(promo and promo.select_one(".card_tag")),
        unit_price=unit.group() if unit else "",
        details=details,
        valid=valid.replace("Galioja:", "").strip(),
        qty=qty,
    )


def scrape(s):
    out, page = [], 1
    while page <= MAX_PAGES:
        data = s.get(API, params={"page": page, "category_id": "", "search": "", "tag": TAG},
                     timeout=30).json()
        soup = BeautifulSoup(data.get("html") or "", "html.parser")
        out += [parse_item(p) for p in soup.select("div.product") if p.select_one("h2")]
        if not data.get("has_more"):
            break
        page += 1
        time.sleep(0.2)
    return out
