from . import aibe, iki, lidl, maxima, rimi

STORES = {
    "Maxima": maxima.scrape,
    "IKI": iki.scrape,
    "Rimi": rimi.scrape,
    "Lidl": lidl.scrape,
    "Aibė": aibe.scrape,
}
