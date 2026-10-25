# Akcijų paieška

Renka akcijų prekes iš Maxima, IKI, Rimi, Lidl ir Aibė ir leidžia jų ieškoti vienoje vietoje,
surikiuotas nuo pigiausios.

## Paleidimas

```
pip install -r requirements.txt
python scrape.py      # surenka akcijas į data/products.json (~1,5 min., ilgiausiai Rimi)
python app.py         # atidaryk http://127.0.0.1:5000
```

Jei `data/products.json` dar nėra, `app.py` duomenis surinks pats. Svetainės apačioje yra mygtukas
„Atnaujinti dabar“.

## Šaltiniai

| Parduotuvė | Iš kur imama | Pastabos |
|---|---|---|
| Maxima | https://www.maxima.lt/pasiulymai (HTML) | Dalis pasiūlymų tik „-30 %“ visai kategorijai, be kainos |
| IKI | `https://iki.lt/wp-json/promos/web-promos?tag=9` (savaitės akcijos, puslapiais) | |
| Rimi | https://www.rimi.lt/e-parduotuve/lt/akcijos (`pageSize=100`, ~50 psl.) | |
| Lidl | https://www.lidl.lt/c/svarbiausios-sios-savaites-akcijos/a10023711 (`data-grid-data` JSON) | |
| Aibė | https://aibe.lt/akcijos/ (HTML) | Sena kaina žinoma tik ten, kur rodoma „Be kortelės“ kaina |

Kiekviena prekė: `store, name, image, url, price, old_price, discount, qty, deal, card, unit_price, details, valid`.
`qty > 1` reiškia, kad `price` yra už kelis vienetus („2 vnt. už“, „2+1“); nuolaida ir rikiavimas
skaičiuojami vienetui. `card: true` – kaina galioja tik su lojalumo kortele.

Kiekvienos parduotuvės kodas yra `scrapers/<parduotuvė>.py`. Jei kuri nors svetainė pasikeičia ir
skreperis nulūžta, likusios veikia toliau, o tos parduotuvės prekės paliekamos iš ankstesnio surinkimo.
