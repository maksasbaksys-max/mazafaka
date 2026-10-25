from bs4 import BeautifulSoup

from .common import bundle_qty, euro, money, product, text

URL = "https://www.maxima.lt/pasiulymai"


def scrape(s):
    soup = BeautifulSoup(s.get(URL, timeout=30).text, "html.parser")
    out = []
    for slide in soup.select("[data-offercard-offer-id]"):
        tag = slide.select_one(".offer-price-tag")
        if not tag:
            continue
        img = slide.select_one(".offer-image img")
        icon = tag.select_one(".offer-price-tag__icon img")
        price = euro(tag.select_one(".offer-price-tag__price-integer"),
                     tag.select_one(".offer-price-tag__price-fraction"))
        deal = text(tag.select_one(".offer-price-tag__benefit"))
        if not deal and price is None:
            # "-30 %" offers on a whole category, no concrete price
            deal = text(tag.select_one(".offer-price-tag__discount")).replace(" ", "")
        out.append(product(
            "Maxima",
            text(slide.select_one("h4")),
            price=price,
            old_price=money(text(tag.select_one(".offer-price-tag__old-price"))),
            image=img.get("src", "") if img else "",
            url=URL,
            deal=deal,
            card=bool(icon and "kortel" in icon.get("alt", "").lower()),
            unit_price=text(slide.select_one(".offer-price-tag__meta-comparison")),
            valid=text(slide.select_one(".offer-price-tag__meta-date")),
            qty=bundle_qty(deal),
        ))
    return out
