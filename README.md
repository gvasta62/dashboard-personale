# Dashboard personale

Pagina iniziale per il browser, in **un unico file HTML** senza librerie né
dipendenze. Funziona aperta da file locale o pubblicata sul web.

👉 **Online:** https://gvasta62.github.io/dashboard-personale/

## Cosa contiene

| Sezione | Note |
|---|---|
| Orologio e data | in italiano, saluto che cambia con l'ora |
| Meteo | via [Open-Meteo](https://open-meteo.com), gratuito e senza chiave API |
| Timer | preset 25/5/15/50 min, avviso sonoro, conto alla rovescia nel titolo della scheda |
| Lista da fare | salvata nel browser |
| Blocco note | testo libero, salvataggio automatico |
| Notizie ANSA | 8 categorie (incl. Umbria), aggiornate ogni 30 min |
| Cambio EUR/JPY | valore, variazione a 7 giorni e sparkline; dati BCE via [Frankfurter](https://frankfurter.dev) |
| Link rapidi | configurabili |
| Citazione casuale | |
| Haiku del giorno | scritto ogni mattina da Claude a partire da data, stagione e meteo di Perugia |

Tema scuro, responsive, funziona su telefono.

## Dove finiscono i dati

Attività e note sono salvate in **`localStorage`**, l'archivio locale del
browser: restano dopo la chiusura, ma **vivono solo sul dispositivo e sul
browser in cui le hai scritte**. Aprendo la pagina dal telefono non vedrai le
note scritte dal PC — non c'è nessun server dietro, e nulla viene inviato
altrove. Svuotare i dati di navigazione ("cookie e dati dei siti") le cancella.

## Come funzionano le notizie

Il browser non può leggere direttamente il feed RSS dell'ANSA: lo vieta la
regola di sicurezza **CORS**, perché ANSA non autorizza altri siti a leggerlo
via JavaScript.

Aggiro l'ostacolo senza servizi-ponte di terzi: lo script `aggiorna_news.py`
gira su GitHub Actions ogni 30 minuti (vedi `.github/workflows/news.yml`),
scarica gli 8 feed e salva `news.json` nel repository. La pagina legge quel
file, che sta sul suo stesso indirizzo — nessun blocco, nessun intermediario.

Per cambiare i notiziari scaricati modifica il dizionario `FEED` in
`aggiorna_news.py`. L'elenco completo è su
[ansa.it/sito/static/ansa_rss.html](https://www.ansa.it/sito/static/ansa_rss.html).

## Come funziona l'haiku del giorno

Ogni mattina alle 6 italiane lo script `genera_haiku.py` gira su GitHub Actions
(vedi `.github/workflows/haiku.yml`), chiede a Claude un haiku nuovo e salva
`haiku.json` nel repository. La pagina legge quel file, come per le notizie.

L'haiku non è generico: allo scrittore vengono passati la data, la stagione e
il meteo di Perugia del giorno (da Open-Meteo, senza chiave), più gli ultimi 25
haiku già scritti — così non si ripete. Ne resta un archivio di 90 dentro
`haiku.json`.

**Serve una chiave API Anthropic**, salvata nei Secrets del repository
(*Settings → Secrets and variables → Actions → New repository secret*) col nome
`ANTHROPIC_API_KEY`. Costo: un haiku al giorno sono pochi centesimi l'anno.

Per cambiare lo stile degli haiku modifica il testo `ISTRUZIONI` in
`genera_haiku.py`.

## Personalizzare

Il file è commentato riga per riga. Tutto ciò che si personalizza sta in due
punti, entrambi segnalati con `PERSONALIZZA`:

- **Colori** — blocco `:root { ... }` all'inizio del CSS
- **Città del meteo, link rapidi, citazioni** — blocchi `A)`, `B)`, `C)`
  all'inizio del JavaScript

Per la città servono latitudine e longitudine: su Google Maps, tasto destro sul
punto → la prima voce del menu sono le due coordinate.

## Usarla come pagina iniziale

Copia l'indirizzo `https://gvasta62.github.io/dashboard-personale/` e incollalo
in:

- **Chrome** — Impostazioni → All'avvio → *Apri una pagina specifica*
- **Firefox** — Impostazioni → Pagina iniziale → *URL personalizzati*
- **Edge** — Impostazioni → Avvio, home e nuove schede → *Apri queste pagine*

Su Android/iOS puoi aggiungerla alla schermata Home dal menu del browser
("Aggiungi a schermata Home").

## Licenza

MIT — fai quello che vuoi.
