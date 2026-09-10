# EPP — Engineering Professional Practice (EX40003, KIIT)

Course material + exam-prep notes for Engineering Professional Practice.
This repo is used from **two machines**; see `.claude/memory/` for synced context.

## Layout
- `LECTURE *.ppt/.pptx`, `COURSE HANDOUT_EPP.docx` — source material from faculty (do not edit)
- `notes/` — plain-text extraction of every deck, regenerate with the tool below
- `study/` — derived revision material (summaries, Q&A, formula sheets)
- `.claude/memory/` — Claude's project memory, tracked in git so it syncs across machines
- `.claude/sync-memory.sh` — run once per machine after cloning to wire memory up
- `.claude/tools/extract-slides.py` — pure-stdlib text extractor

## Reading the slides
This machine has no LibreOffice, no pip and no sudo, so the usual converters are unavailable.
`extract-slides.py` handles all three formats with only the standard library — a ZIP+XML
reader for `.pptx`/`.docx` and an OLE compound-file + PowerPoint record parser for legacy `.ppt`:

```bash
python3 .claude/tools/extract-slides.py *.ppt *.pptx *.docx
```

Titles come out prefixed `# `, body text indented. Note that a number of slides hold their
content as **images or equation objects** and extract as blank — `.claude/memory/epp-slide-content-gaps.md`
lists which ones and records the reconstructed values.

## New machine setup
```bash
git clone git@github.com:thisizaro/EPP-7th-Sem.git && cd EPP-7th-Sem
bash .claude/sync-memory.sh
```
