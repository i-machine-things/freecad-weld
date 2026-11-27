# Coding Best Practices & Reminders

> **Style rule:** Notes must be clear and concise — 300 characters or less each. Group by topic, not by date. Whenever a PR review (CodeRabbit or human) catches a mistake, add or amend a note here right away so it isn't repeated.

## Addon Manager metadata

- `package.xml`'s `readme` URL takes the raw Markdown (`.../raw/<branch>/README.md`), not the `blob` page: the Addon Manager fetches and renders the Markdown itself, logs that it expects raw, and rewrites `/blob/` to `/raw/` anyway.
- Only link URLs in docs that already resolve. A link to a site published in the same change (e.g. the catalog on GitHub Pages) reads as a 404 to a reviewer until it goes live; publish first, or say it is coming.
