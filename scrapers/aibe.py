from bs4 import BeautifulSoup

from .common import euro, money, product, text

URL = "https://aibe.lt/akcijos/"


def scrape(s):
    soup = BeautifulSoup(s.get(URL, timeout=30).text, "html.parser")
    out, seen = [], set()
    for b in soup.select(".bestOffers-block[data-id]"):
        if b["data-id"] in seen:
            continue
        seen.add(b["data-id"])
        img = b.select_one(".bestOffers-block-discountProduct-imgWrapper img")
        no_card = b.select_one(".discount-without-card-price")
        out.append(product(
            "Aibė",
            text(b.select_one(".bestOffers-block-discountProduct-name")),
            price=euro(b.select_one(".discount-price-now-euro"),
                       b.select_one(".discount-price-now-cent")),
            # Aibė shows only the card-less price; there is no "regular price" otherwise
            old_price=money(text(no_card)),
            image=(img.get("data-src") or img.get("src", "")) if img else "",
            url=URL,
            card=bool(no_card),
            unit_price=text(b.select_one(".price_quantity-text")),
        ))
    return out
