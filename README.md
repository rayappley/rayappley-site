# rayappley – túraútmutatók

A rayappley.com leendő oldala. Jekyll-oldal: a GitHub Pages magától felépíti, neked csak commitolni és pusholni kell (GitHub Desktop).

Amíg a `_config.yml`-ben `launched: false` áll, a keresők nem indexelik az oldalt. A repó viszont publikus, vagyis a link ismeretében bárki megnézheti.

## Első beállítás (egyszer kell)

1. **GitHub Desktop:** File → New repository. Név: `rayappley-site`, hely: `Documents/GitHub`. Create.
2. Másold bele ennek a mappának a tartalmát (vagy Claude bemásolja).
3. **GitHub Desktop:** Commit to main → Publish repository. Kapcsold ki a „Keep this code private” jelölőt, mert az ingyenes GitHub Pages csak publikus repóval működik.
4. **github.com** → a repó → Settings → Pages:
   - Source: *Deploy from a branch*
   - Branch: `main` / `(root)`
   - Save
5. A `CNAME` fájl miatt a GitHub magától a `rayappley.com` címre teszi az oldalt. Amint a DNS beállt, ott él.

## Mi hol van

| Mappa / fájl | Mi van benne |
| --- | --- |
| `_guides/` | Az útmutatók. Egy fájl = egy cikk (Markdown). |
| `assets/img/` | Képek. Útmutatónként érdemes egy almappát nyitni, pl. `assets/img/whw/`. |
| `assets/css/main.css` | Kinézet: színek, betűk, elrendezés. A tetején vannak a változók. |
| `index.html` | Főoldal |
| `about/` | Rólam oldal |
| `privacy/` | Adatvédelmi tájékoztató (Privacy Policy) |
| `maps/` | Térképek oldal, egyelőre rejtve (`published: false`) |
| `_config.yml` | Az oldal beállításai: név, cím, launched kapcsoló |
| `_layouts/`, `_includes/` | Sablonok. Ezekhez általában nem kell nyúlni. |
| `tools/preview.py` | Offline előnézet. Claude ezzel ellenőrzi a kinézetet, neked nem kell. |

## Új útmutató

1. Másolj le egy fájlt a `_guides/` mappában, és nevezd át (pl. `ushuaia.md`). A fájlnévből lesz a link: `/guides/ushuaia/`.
2. A fájl tetején, a `---` jelek között vannak az adatok (cím, ország, táv, napok, borítókép stb.). Amit nem tudsz, azt töröld ki: a sor eltűnik az oldalról.
   - `published: false` = a cikk nem jelenik meg az oldalon. Most így van rejtve a WHW és a Svaneti vázlat.
   - `hero:` a borítókép, `card_image:` a kártyakép a főoldalon (ha nincs, a borítókép lesz). Ha egyik sincs, a cikk kép nélkül jelenik meg.
3. `order:` adja a sorrendet (időrendben haladunk).
4. `status: draft` piros „Work in progress” sávot tesz a cikk tetejére. Ha kész, töröld ki.
5. Alatta jön a szöveg Markdownban: `## Alcím`, `**félkövér**`, `- lista`, táblázat `|` jelekkel.

Kép beszúrása a szövegbe:

```
{% include photo.html src="/assets/img/whw/day5.jpg" alt="Tent facing Buachaille Etive Mòr" caption="Our day 5 camp" %}
```

Képek: JPG, kb. 2000 px széles, lehetőleg 500 KB alatt.

## Szerkesztés telefonról

github.com → repó → nyisd meg a fájlt → ceruza ikon → szerkeszd → *Commit changes*. Kb. 1 perc múlva frissül az oldal.

## Betűtípus csere

A címekhez most a **Bricolage Grotesque** van beállítva (ingyenes Google Font, magyar ékezetekkel). Csere:

1. `_includes/head.html`: írd át a Google Fonts linket.
2. `assets/css/main.css`: írd át a `--font-display` sort.

Saját betűfájl (pl. .woff2) az `assets/fonts/` mappába mehet. Előtte nézd meg, hogy a licence engedi-e a webes használatot.

## Indulás

1. ✓ Domain: `rayappley.com` (Porkbun, auto-renew).
2. ✓ Repó létrehozva, a fájlok bemásolva. `_config.yml`-ben már a `rayappley.com` cím áll, és van `CNAME` fájl.
3. Publish repository (publikus) → Settings → Pages: *Deploy from a branch*, `main` / `(root)`. A Custom domain mezőben a `rayappley.com`-nak kell állnia.
4. Porkbun DNS: a GitHub Pages rekordjai (Claude megadja). Ha a domain zöld pipát kapott, kapcsold be az *Enforce HTTPS*-t.
5. Képek: a W Trek borítóképe (ez lesz a kártyakép is), plusz pár kép a cikkbe.
6. Élesítés: `_config.yml` → `launched: true`. Ettől kezdve indexelhetik a keresők.
7. Google Search Console → domain hozzáadása → sitemap beküldése (`https://rayappley.com/sitemap.xml`).

## Licencek

- A fotók az enyémek.
- Az OpenStreetMapből származó útvonal- és térképadatoknál fel kell tüntetni: „© OpenStreetMap contributors” (ODbL). Ha ilyen térkép kerül egy cikkbe, az ábra alatti feliratba írd bele. A W Trek térképe saját rajz, ahhoz nem kell.
