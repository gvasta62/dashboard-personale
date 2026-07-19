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
| Link rapidi | configurabili |
| Citazione casuale | |

Tema scuro, responsive, funziona su telefono.

## Dove finiscono i dati

Attività e note sono salvate in **`localStorage`**, l'archivio locale del
browser: restano dopo la chiusura, ma **vivono solo sul dispositivo e sul
browser in cui le hai scritte**. Aprendo la pagina dal telefono non vedrai le
note scritte dal PC — non c'è nessun server dietro, e nulla viene inviato
altrove. Svuotare i dati di navigazione ("cookie e dati dei siti") le cancella.

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
