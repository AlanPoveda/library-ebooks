# 📚 Library Transformer

Convert PDFs into clean, readable e-books — fix broken hyphenation,
optionally check/fix grammar, and optionally translate — all running
**100% locally** on your own machine. Drag a PDF into a small local
web app, pick your options, download an EPUB (and optionally AZW3 for
Kindle) when it's done.

No file ever leaves your computer. No cloud APIs, no accounts, no
telemetry.

## Why this exists

PDF-to-e-reader conversion tools routinely leave justified-text PDFs
with words split by a hyphen at the end of a line (e.g. `informa-`
/ `tion`), because that's how the original PDF was typeset. Most
converters don't fix this, so the resulting EPUB is full of
mid-sentence hyphens that make it unpleasant to read. This project
started as a fix for that one problem, then grew into a small local
pipeline that also handles grammar review and translation — all
offline, using open-source tools already running on your machine.

## Features

- **PDF → EPUB** (and optional **AZW3** for Kindle), via
  [Calibre](https://calibre-ebook.com/)
- **Hyphenation repair**: rejoins words broken across line wraps,
  validated against a real dictionary (pt/es/en) so legitimate
  hyphenated compounds (like *guarda-chuva*) are left alone
- **Grammar check & auto-fix** (optional): runs
  [LanguageTool](https://languagetool.org/) locally, auto-applies
  high-confidence corrections, and reports what's left in a
  linter-style file
- **Translation** (optional): fully offline via
  [Argos Translate](https://www.argosopentech.com/), with automatic
  pivot-language fallback (e.g. pt→en→es) when no direct language
  pack exists
- **Simple local web UI**: drag-and-drop upload, live progress per
  pipeline step, download links when done — interface available in
  Portuguese, English, and Spanish
- **Double-click launcher for macOS** — no terminal needed day-to-day
  (see [Packaging](#packaging-a-macos-app) below)

## How it works

```
PDF (drag & drop)
  │
  ▼
[1] PDF → EPUB                (Calibre)
  │
  ▼
[2] Fix broken hyphenation    (dictionary-aware, pt/es/en)
  │
  ▼
[3] Grammar check/fix?        (LanguageTool, optional)
  │
  ▼
[4] Translate?                (Argos Translate, optional)
  │
  ▼
[5] EPUB → AZW3?               (Calibre, optional)
  │
  ▼
Download: EPUB (+ AZW3, + grammar report if applicable)
```

Each step is an independent, tested Python module. See
[`PLANNING.md`](PLANNING.md) for the full architecture, design
decisions, and known trade-offs discovered along the way (there are a
few honest ones — real-world testing surfaced things unit tests alone
didn't catch).

## Requirements

This project was built and tested on **macOS**. It should mostly work
on Linux with minor changes (the Calibre auto-detection path and the
`.app` packaging script are macOS-specific); Windows is untested.

- Python 3.11+
- [Calibre](https://calibre-ebook.com/) — installed as a regular
  desktop app (used as the PDF/EPUB/AZW3 conversion engine)
- Java, via `brew install openjdk` — only needed if you use the
  grammar-check feature (runs a local LanguageTool server)
- `enchant`, via `brew install enchant` — dictionaries used for
  hyphenation repair

## Installation

```bash
git clone https://github.com/AlanPoveda/library-ebooks.git
cd library-ebooks

brew install enchant
brew install openjdk
echo 'export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"' >> ~/.zshrc

python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Calibre needs to be installed separately from
[calibre-ebook.com](https://calibre-ebook.com/) (or `brew install --cask calibre`).

## Usage

### Run the server directly

```bash
source .venv/bin/activate
export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"
uvicorn library_ebooks.app:app --reload
```

Open **http://127.0.0.1:8000/**, drag a PDF, pick your options, hit
Convert.

### Packaging a macOS app

If you'd rather not touch the terminal day-to-day, build a
double-clickable app:

```bash
./packaging/build_macos_app.sh
```

This creates two apps on your Desktop:

- **Library Transformer.app** — starts the server (if it isn't
  already running) and opens it in your browser.
- **Stop Library Transformer.app** — stops the server.

macOS will likely warn that each is from an "unidentified developer"
the first time — right-click → Open once per app to allow it.

Closing the browser tab does **not** stop the server — it's a
background process independent of the tab (and a conversion might
still be running). Use **Stop Library Transformer.app** when you're
done, or run `lsof -ti:8800 | xargs kill` from a terminal.

## Running tests

```bash
pytest
```

## Known limitations

- **Translation is slow for full books.** It runs entirely on CPU —
  measured at roughly 20–30 minutes for a ~150,000-word book. This is
  proportional to the actual amount of text (confirmed by direct
  measurement, not per-call overhead), so batching wouldn't help; only
  GPU acceleration or a smaller model would.
- **This is a local, single-user tool by design**, not a hosted
  service — it assumes Calibre/Java are installed locally, keeps job
  state in memory, and writes output to a local folder. It is not
  meant to be deployed to serverless platforms (see `PLANNING.md` for
  why).
- macOS-first: the Calibre bundle auto-detection and the `.app`
  packaging script assume macOS conventions.

## Project structure

```
library-ebooks/
├── src/library_ebooks/
│   ├── convert.py       # Calibre wrapper (PDF↔EPUB↔AZW3)
│   ├── dehyphenate.py   # hyphenation repair
│   ├── translate.py     # Argos Translate wrapper + pivot fallback
│   ├── lint.py          # LanguageTool wrapper + auto-corrections
│   ├── pipeline.py      # orchestrates all of the above
│   ├── app.py           # FastAPI app (upload, progress, download)
│   └── static/          # drag-and-drop UI (HTML/CSS/JS, i18n)
├── tests/                # 120+ tests, TDD throughout
├── packaging/            # macOS .app builder
└── PLANNING.md           # architecture, decisions, and trade-offs
```

## Development

Built test-first throughout: for every module, tests were written
before the implementation, and every real dependency (Calibre,
LanguageTool, Argos Translate) was validated against the real tool at
least once, not just mocks. `PLANNING.md` documents a handful of real
bugs and trade-offs found that way (an `ebooklib` TOC bug, aspell's
weak hyphenated-compound coverage in ES/EN, translation throughput,
and others).

## Contributing

Issues and pull requests are welcome. For anything non-trivial, please
open an issue first to discuss the approach.

## Acknowledgements

This project is a thin, opinionated orchestration layer over great
existing open-source tools:

- [Calibre](https://calibre-ebook.com/) — e-book conversion engine
- [Argos Translate](https://www.argosopentech.com/) — offline
  neural machine translation
- [LanguageTool](https://languagetool.org/) — grammar and style
  checking
- [enchant](https://abiword.github.io/enchant/) / aspell — spell
  dictionaries

## License

[MIT](LICENSE)
