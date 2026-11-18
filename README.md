# From the Heel of Italy

Sito di aggiornamenti per sostenitori — https://fromtheheelofitaly.org

## Struttura

| Cartella / file | Cosa contiene |
|---|---|
| `site.json` | Nome, sottotitolo, link di iscrizione, social e le 5 aree |
| `content/posts/` | Gli aggiornamenti (un file `.md` per articolo) |
| `content/pages/` | Pagine fisse: About, Support, Privacy |
| `static/` | CSS, logo e immagini (`static/images/`) |
| `build.py` | Genera il sito |
| `public/` | Il sito finito, pubblicato da Cloudflare Pages |

## Aggiungere un aggiornamento

1. Carica le foto in `static/images/` (es. `2026-12-rifugio-campo.jpg`).
2. Crea `content/posts/AAAA-MM-GG-titolo-breve.md`:

```markdown
---
title: Titolo dell'articolo
date: 2026-12-05
area: il-rifugio
cover: /images/2026-12-rifugio-campo.jpg
excerpt: Una o due frasi di riassunto.
video: https://www.youtube.com/watch?v=XXXXXXXXXXX
---

Testo dell'articolo (300–400 parole)...
```

Aree valide: `family`, `church`, `il-rifugio`, `missions`, `plant-and-strengthen`
(lasciare vuoto per una notizia generale). Un link YouTube su una riga da solo diventa un video incorporato.

3. Esegui `python3 build.py` (serve `pip install markdown`) e fai commit anche della cartella `public/`.

## Cloudflare Pages

- Framework preset: *None*
- Build command: *(vuoto)*
- Build output directory: `public`
