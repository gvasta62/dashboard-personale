# -*- coding: utf-8 -*-
"""
genera_haiku.py
---------------
Ogni giorno chiede a Claude di comporre un haiku nuovo e lo salva in
haiku.json, accanto alla dashboard. La pagina legge quel file e mostra
l'haiku del giorno.

L'haiku non e' generico: allo scrittore vengono passati la data di oggi,
la stagione e il tempo che fa a Perugia, cosi' il testo parla davvero
di questa giornata. Gli ultimi haiku scritti vengono passati anche loro,
come promemoria di cosa NON ripetere.

Non gira sul tuo computer: lo lancia GitHub ogni notte (vedi il file
.github/workflows/haiku.yml). Cosi' l'haiku c'e' anche a PC spento.

Per provarlo a mano dal tuo computer:

    pip install anthropic
    set ANTHROPIC_API_KEY=la-tua-chiave        (su Windows)
    python genera_haiku.py
"""

# ============================================================================
# SEZIONE 1 - Gli attrezzi che servono
# ============================================================================

import json                     # per leggere e scrivere haiku.json
import os                       # per leggere la chiave API dall'ambiente
import sys                      # per uscire con un messaggio d'errore
import urllib.request           # per chiedere il meteo (nessuna libreria extra)
from datetime import datetime, timezone, timedelta

import anthropic                # la libreria ufficiale di Claude


# ============================================================================
# SEZIONE 2 - Impostazioni
# ============================================================================

FILE_HAIKU = "haiku.json"

# Le coordinate di Perugia, le stesse che la dashboard usa per il meteo.
CITTA = "Perugia"
LATITUDINE = 43.1107
LONGITUDINE = 12.3908

# Quanti haiku vecchi conservare nell'archivio dentro haiku.json.
QUANTI_CONSERVARE = 90

# Quanti haiku recenti mostrare a Claude perche' non si ripeta.
QUANTI_MOSTRARE = 25

# Il fuso orario italiano rispetto a UTC. GitHub lavora in UTC: senza
# questa correzione, un lancio a mezzanotte scriverebbe la data sbagliata.
# (+2 in estate, +1 in inverno: la differenza e' irrilevante per la data,
#  perche' il workflow gira alle 4 del mattino UTC.)
FUSO_ITALIA = timezone(timedelta(hours=2))


# ============================================================================
# SEZIONE 3 - Il contesto della giornata: data, stagione, meteo
# ============================================================================

MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
        "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]

GIORNI = ["lunedi'", "martedi'", "mercoledi'", "giovedi'",
          "venerdi'", "sabato", "domenica"]


def stagione_di(data):
    """Restituisce la stagione di una data (approssimazione ai giorni 21)."""
    mese, giorno = data.month, data.day
    if (mese, giorno) >= (12, 21) or (mese, giorno) < (3, 21):
        return "inverno"
    if (mese, giorno) < (6, 21):
        return "primavera"
    if (mese, giorno) < (9, 23):
        return "estate"
    return "autunno"


# I codici meteo di Open-Meteo (standard WMO), tradotti in italiano.
# Sono gli stessi che usa la scheda del meteo nella dashboard.
CONDIZIONI = {
    0: "cielo sereno", 1: "poco nuvoloso", 2: "parzialmente nuvoloso",
    3: "coperto", 45: "nebbia", 48: "nebbia con brina",
    51: "pioviggine leggera", 53: "pioviggine", 55: "pioviggine intensa",
    61: "pioggia leggera", 63: "pioggia", 65: "pioggia forte",
    71: "neve leggera", 73: "neve", 75: "neve abbondante",
    80: "rovesci leggeri", 81: "rovesci", 82: "rovesci violenti",
    95: "temporale", 96: "temporale con grandine", 99: "temporale violento",
}


def meteo_di_oggi():
    """Chiede a Open-Meteo il tempo previsto oggi a Perugia.

    Non serve alcuna chiave: Open-Meteo e' gratuito e aperto.
    Se il servizio non risponde restituiamo None: l'haiku si scrivera'
    comunque, semplicemente senza parlare del tempo.
    """
    indirizzo = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LATITUDINE}&longitude={LONGITUDINE}"
        "&daily=weather_code,temperature_2m_max,temperature_2m_min"
        "&timezone=Europe%2FRome&forecast_days=1"
    )
    try:
        with urllib.request.urlopen(indirizzo, timeout=20) as risposta:
            dati = json.load(risposta)
        giorno = dati["daily"]
        return {
            "condizioni": CONDIZIONI.get(giorno["weather_code"][0], "tempo vario"),
            "minima": round(giorno["temperature_2m_min"][0]),
            "massima": round(giorno["temperature_2m_max"][0]),
        }
    except Exception as errore:
        print(f"  meteo non disponibile ({errore}) - proseguo senza")
        return None


def descrivi_oggi(oggi):
    """Mette insieme una frase che descrive la giornata, per Claude."""
    righe = [
        f"Oggi e' {GIORNI[oggi.weekday()]} {oggi.day} {MESI[oggi.month - 1]} "
        f"{oggi.year}. Siamo in {stagione_di(oggi)}."
    ]
    meteo = meteo_di_oggi()
    if meteo:
        righe.append(
            f"A {CITTA} il tempo di oggi: {meteo['condizioni']}, "
            f"da {meteo['minima']} a {meteo['massima']} gradi."
        )
    return "\n".join(righe)


# ============================================================================
# SEZIONE 4 - L'archivio: leggere quello che c'era prima
# ============================================================================

def leggi_archivio():
    """Legge haiku.json se esiste, altrimenti parte da zero.

    Restituisce la lista degli haiku gia' scritti, dal piu' recente.
    """
    if not os.path.exists(FILE_HAIKU):
        return []
    try:
        with open(FILE_HAIKU, encoding="utf-8") as file:
            return json.load(file).get("archivio", [])
    except (json.JSONDecodeError, OSError) as errore:
        print(f"  haiku.json illeggibile ({errore}) - riparto da zero")
        return []


# ============================================================================
# SEZIONE 5 - La richiesta a Claude
# ============================================================================

# Le istruzioni di fondo: chi e' lo scrittore e che regole segue.
# Questo testo non cambia mai da un giorno all'altro.
ISTRUZIONI = """Sei un poeta italiano che compone un haiku ogni giorno.

Regole della forma:
- tre versi, di 5, 7 e 5 sillabe (conta le sillabe poetiche italiane,
  con le sinalefi: vocale finale e vocale iniziale della parola dopo
  contano come una sola sillaba)
- niente titolo, niente rime, niente punto finale
- un'immagine concreta, osservata: una cosa che si vede, si sente o si
  tocca. Non concetti astratti, non morali, non spiegazioni
- un solo momento, fermo. L'haiku mostra, non racconta

Regole del contenuto:
- parla della giornata che ti viene descritta: la stagione, la luce,
  il tempo che fa, quello che succede fuori in questo periodo dell'anno
- resta ancorato all'Italia centrale, alla campagna e alla citta' di
  Perugia: ulivi, colline, tetti, piazze, non ciliegi giapponesi
- niente parole inglesi, niente emoji, niente parentesi

Rispondi ESATTAMENTE cosi', senza aggiungere altro:

<haiku>
primo verso
secondo verso
terzo verso
</haiku>
<nota>una frase breve, max 15 parole, che dice cosa hai osservato</nota>"""


def estrai(testo, etichetta):
    """Prende il contenuto fra <etichetta> e </etichetta>.

    Facciamo a mano questo piccolo ritaglio invece di usare librerie:
    il formato e' semplice e cosi' si capisce cosa succede.
    """
    apertura = f"<{etichetta}>"
    chiusura = f"</{etichetta}>"
    inizio = testo.find(apertura)
    fine = testo.find(chiusura)
    if inizio == -1 or fine == -1:
        return None
    return testo[inizio + len(apertura):fine].strip()


def chiedi_haiku(contesto, precedenti):
    """Chiede a Claude l'haiku di oggi. Restituisce (testo, nota)."""

    # Il client legge da solo la chiave dalla variabile d'ambiente
    # ANTHROPIC_API_KEY: la chiave non compare mai dentro il codice.
    client = anthropic.Anthropic()

    # Costruiamo il messaggio: il contesto di oggi + cosa non ripetere.
    richiesta = [contesto, ""]
    if precedenti:
        richiesta.append("Haiku che hai gia' scritto nei giorni scorsi. "
                         "Non ripetere queste immagini ne' queste parole "
                         "chiave, cerca qualcosa di nuovo da guardare:")
        richiesta.append("")
        for voce in precedenti:
            # Rientriamo i versi cosi' si distinguono dal resto.
            righe_indentate = "\n".join("  " + r for r in voce["testo"].split("\n"))
            richiesta.append(f"({voce['data']})\n{righe_indentate}\n")
    richiesta.append("Scrivi l'haiku di oggi.")

    risposta = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1000,
        system=ISTRUZIONI,
        messages=[{"role": "user", "content": "\n".join(richiesta)}],
    )

    # La risposta e' una lista di "blocchi": prendiamo quelli di testo.
    testo_risposta = "".join(
        blocco.text for blocco in risposta.content if blocco.type == "text"
    )

    haiku = estrai(testo_risposta, "haiku")
    nota = estrai(testo_risposta, "nota")

    if not haiku:
        raise SystemExit(
            "Claude non ha risposto nel formato atteso, non scrivo il file.\n"
            f"Risposta ricevuta:\n{testo_risposta}"
        )

    # Teniamo solo le prime tre righe non vuote: e' un haiku, non un poema.
    versi = [riga.strip() for riga in haiku.split("\n") if riga.strip()][:3]
    return "\n".join(versi), (nota or "")


# ============================================================================
# SEZIONE 6 - Il programma vero e proprio
# ============================================================================

def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Manca la chiave: imposta la variabile ANTHROPIC_API_KEY.")

    oggi = datetime.now(FUSO_ITALIA).date()
    data_oggi = oggi.isoformat()          # esempio: "2026-07-19"

    archivio = leggi_archivio()

    # Se l'haiku di oggi esiste gia', non ne chiediamo un altro: cosi'
    # possiamo rilanciare lo script senza sprecare una chiamata.
    if archivio and archivio[0].get("data") == data_oggi:
        print(f"L'haiku del {data_oggi} c'e' gia', non faccio nulla.")
        return

    print(f"Compongo l'haiku del {data_oggi}...")
    contesto = descrivi_oggi(oggi)
    print(contesto)

    testo, nota = chiedi_haiku(contesto, archivio[:QUANTI_MOSTRARE])

    print()
    print(testo)
    if nota:
        print(f"  ({nota})")

    # Il nuovo haiku va in cima all'archivio; teniamo solo i piu' recenti.
    archivio.insert(0, {"data": data_oggi, "testo": testo, "nota": nota})
    archivio = archivio[:QUANTI_CONSERVARE]

    risultato = {
        "aggiornato": datetime.now(timezone.utc).isoformat(),
        "data": data_oggi,
        "testo": testo,
        "nota": nota,
        "archivio": archivio,
    }

    with open(FILE_HAIKU, "w", encoding="utf-8") as file:
        # ensure_ascii=False tiene le lettere accentate leggibili nel file.
        json.dump(risultato, file, ensure_ascii=False, indent=1)

    print(f"\n{FILE_HAIKU} scritto ({len(archivio)} haiku in archivio).")


if __name__ == "__main__":
    main()
