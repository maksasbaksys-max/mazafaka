import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .common import bundle_qty, euro, money, product, text

URL = "https://www.rimi.lt/e-parduotuve/lt/akcijos"
PAGE_SIZE = 100
WORKERS = 4


def parse_item(it):
    link = it.select_one("a.card__url")
    img = it.select_one(".card__image-wrapper img")
    regular = money(text(it.select_one(".card__price .sr-only")))
    label = it.select_one(".price-label")
    if label:
        # Promo label (usually "Mano Rimi" card price); the main price is then the regular one
        price = euro(label.select_one(".major"), label.select_one(".cents"))
        old = money(text(label.select_one(".price-label__old-price"))) or regular
        deal = " ".join(filter(None, [text(label.select_one(".price-label__text")),
                                      text(label.select_one(".price-label__header"))]))
        card = bool(label.select_one('img[src*="rimi-card"]'))
        unit = text(label.select_one(".price-per-unit"))
    else:
        price = regular
        old = money(text(it.select_one(".old-price-tag .sr-only")))
        deal, card = "", False
        unit = text(it.select_one(".card__price-per [aria-hidden]"))
    image = (img.get("data-src") or img.get("src", "")) if img else ""
    # w_auto/dpr_auto need browser client hints; ask Cloudinary for a fixed thumbnail
    image = image.replace("dpr_auto", "dpr_1").replace("w_auto", "w_300,h_300")
    return product(
        "Rimi",
        text(it.select_one(".card__name")),
        price=price,
        old_price=old,
        image=image,
        url=urljoin(URL, link["href"]) if link else URL,
        deal=deal,
        card=card,
        unit_price=unit,
        qty=bundle_qty(deal),
    )


def fetch_page(s, page):
    html = s.get(URL, params={"pageSize": PAGE_SIZE, "currentPage": page}, timeout=60).text
    soup = BeautifulSoup(html, "html.parser")
    items = [parse_item(it) for it in soup.select(".product-grid__item")
             if it.select_one(".card__name")]
    pages = [int(a["data-page"]) for a in soup.select(".pagination a[data-page]")]
    return items, max(pages + [page])


def scrape(s):
    out, last = fetch_page(s, 1)

    def worker(page):
        time.sleep(0.2 * (page % WORKERS))
        return fetch_page(s, page)[0]

    with ThreadPoolExecutor(WORKERS) as pool:
        for items in pool.map(worker, range(2, last + 1)):
            out += items
    return out
