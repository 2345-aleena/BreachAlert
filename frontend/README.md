# BreachAlert — Week 1: Frontend

A static, semantic, accessible landing page for BreachAlert — a personal
security-scan tool that checks breach exposure and password strength and
turns it into a single, trackable score.

## Project structure

```
breachalert/
├── index.html      # Semantic markup — header/main/footer, one h1
├── styles.css       # Design tokens, Grid (macro layout) + Flexbox (components)
├── script.js         # Mobile nav, form validation, back-to-top — no dependencies
├── server.py          # Local dev server (Python standard library only)
└── README.md
```

## Run it

You need Python 3 installed (any recent version — nothing else required,
no `pip install` needed).

1. Open this folder in VS Code.
2. Open a terminal in VS Code: **Terminal → New Terminal**.
3. Run:

   ```bash
   python server.py
   ```

   (On some systems it's `python3 server.py` instead.)

4. Your browser should open automatically to `http://localhost:8000`.
   If it doesn't, open that URL manually.
5. To stop the server, go back to the terminal and press `Ctrl+C`.

> Why not just double-click `index.html`? Opening it directly via
> `file://` works for now, but breaks once you start calling APIs from
> `script.js` in Week 2 — browsers block those requests from local
> files for security reasons. Running it through `server.py` avoids
> that problem from day one.

## What's implemented (Week 1 checklist)

- [x] Semantic HTML: `header`, `nav`, `main`, `footer`, one `<h1>`
- [x] No skipped heading levels (h1 → h2 → h3)
- [x] External CSS only, zero inline styles, no ID-based styling
- [x] CSS Grid for page-level layout, Flexbox for component alignment
- [x] Responsive down to mobile, with a working hamburger menu
- [x] Keyboard accessible: visible focus states, skip link, Escape closes menu
- [x] Form validation with inline, specific error messages
- [x] Live status region (`aria-live`) so the scan "loading" state is
      announced to screen readers, not just shown visually
- [x] AA color contrast on all text
- [x] `prefers-reduced-motion` respected

## Where the backend plugs in (Week 2+)

The scan form in `index.html` (`#scan-form`) currently simulates a scan
with a `setTimeout` in `script.js`. When your API is ready:

1. Replace the `setTimeout` block in `script.js` with a real `fetch()`
   call to your breach-check endpoint.
2. Replace the hardcoded `72` score in the hero's `.scan-card` with a
   value rendered from the API response.
3. Keep the same loading/success/error UI states already built — just
   swap what triggers them.

## Notes

- The usage numbers in the "stats strip" section (2.4M scans, etc.)
  are placeholder copy for the mockup — swap them for real numbers
  once you have them, or remove the section.
- Fonts are loaded from Google Fonts (Space Grotesk, Inter,
  JetBrains Mono) via CDN — requires an internet connection to render
  correctly. For a fully offline setup later, self-host the font files.
