#!/usr/bin/env python3
"""
Scarica i notiziari RSS dell'ANSA e li salva in un unico file news.json.

Perche' esiste questo script
----------------------------
Una pagina web non puo' leggere direttamente il feed dell'ANSA: il browser
lo impedisce per una regola di sicurezza chiamata CORS (il sito ANSA non
autorizza esplicitamente altri siti a leggere i suoi contenuti via
JavaScript).

La soluzione: questo script gira su GitHub ogni mezz'ora, scarica i feed
e ne salva una copia in news.json dentro il sito stesso. La dashboard
legge quel file, che sta sul suo stesso indirizzo, e nessuno la blocca.

Usa solo la libreria standard di Python: nessuna installazione richiesta.
"""

import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

# Quante notizie tenere per ogni categoria.
MASSIMO_PER_CATEGORIA = 12

# I notiziari da scaricare: chiave interna -> (nome mostrato, indirizzo).
# Per aggiungerne uno, copia una riga: trovi l'elenco completo dei feed
# ANSA su https://www.ansa.it/sito/static/ansa_rss.html
FEED = {
    "ultimaora":  ("Ultima ora", "https://www.ansa.it/sito/notizie/topnews/topnews_rss.xml"),
    "umbria":     ("Umbria",     "https://www.ansa.it/umbria/notizie/umbria_rss.xml"),
    "cronaca":    ("Cronaca",    "https://www.ansa.it/sito/notizie/cronaca/cronaca_rss.xml"),
    "politica":   ("Politica",   "https://www.ansa.it/sito/notizie/politica/politica_rss.xml"),
    "economia":   ("Economia",   "https://www.ansa.it/sito/notizie/economia/economia_rss.xml"),
    "mondo":      ("Mondo",      "https://www.ansa.it/sito/notizie/mondo/mondo_rss.xml"),
    "tecnologia": ("Tecnologia", "https://www.ansa.it/sito/notizie/tecnologia/tecnologia_rss.xml"),
    "sport":      ("Sport",      "https://www.ansa.it/sito/notizie/sport/sport_rss.xml"),
}


def scarica(indirizzo):
    """Scarica il contenuto di un indirizzo e lo restituisce come testo."""
    richiesta = urllib.request.Request(
        indirizzo,
        # Alcuni siti rifiutano le richieste che non dichiarano un browser.
        headers={"User-Agent": "dashboard-personale/1.0 (+https://github.com/gvasta62/dashboard-personale)"},
    )
    with urllib.request.urlopen(richiesta, timeout=30) as risposta:
        return risposta.read()


def data_iso(testo):
    """Converte la data del feed (formato email) nel formato standard ISO.

    Se la conversione fallisce restituisce None: meglio una notizia senza
    orario che un intero aggiornamento andato a monte.
    """
    if not testo:
        return None
    try:
        return parsedate_to_datetime(testo).astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError):
        return None


def leggi_feed(indirizzo):
    """Estrae titolo, link e data da ogni notizia del feed."""
    radice = ET.fromstring(scarica(indirizzo))
    voci = []

    # La struttura di un RSS e': <rss><channel><item>...</item></channel></rss>
    # findall trova tutti gli <item>; [:N] tiene solo i primi N.
    for item in radice.findall(".//item")[:MASSIMO_PER_CATEGORIA]:
        titolo = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        if not titolo or not link:
            continue  # una notizia senza titolo o senza link non ci serve
        voci.append({
            "titolo": titolo,
            "link": link,
            "data": data_iso(item.findtext("pubDate")),
        })
    return voci


def main():
    categorie = {}
    errori = []

    for chiave, (nome, indirizzo) in FEED.items():
        try:
            voci = leggi_feed(indirizzo)
            if voci:
                categorie[chiave] = {"nome": nome, "voci": voci}
                print(f"  {nome:<12} {len(voci)} notizie")
            else:
                errori.append(f"{nome}: feed vuoto")
        except Exception as errore:
            # Se un feed non risponde tiriamo dritto con gli altri:
            # meglio una dashboard con 7 categorie su 8 che nessuna.
            errori.append(f"{nome}: {errore}")
            print(f"  {nome:<12} ERRORE: {errore}")

    if not categorie:
        raise SystemExit("Nessun feed scaricato: non aggiorno news.json")

    risultato = {
        "aggiornato": datetime.now(timezone.utc).isoformat(),
        "fonte": "ANSA.it",
        "categorie": categorie,
    }
    if errori:
        risultato["errori"] = errori

    with open("news.json", "w", encoding="utf-8") as file:
        # ensure_ascii=False tiene le lettere accentate leggibili nel file.
        json.dump(risultato, file, ensure_ascii=False, indent=1)

    print(f"news.json scritto: {len(categorie)} categorie")


if __name__ == "__main__":
    main()
