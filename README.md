# Toptastic Bot

Automated scraper + enricher that collects the UK Singles Chart each week, stores it in a SQLite database (`songs.db`), and enriches rows with YouTube video IDs. A GitHub Actions workflow publishes the latest database to GitHub Pages along with integrity metadata.

## Public Data Artifacts

After the Pages workflow has run successfully, the latest files are available at (replace `mjdavy` and repo name if you fork):

```text
https://mjdavy.github.io/toptastic-bot/songs.db
https://mjdavy.github.io/toptastic-bot/songs.sha256
https://mjdavy.github.io/toptastic-bot/timestamp.txt
https://mjdavy.github.io/toptastic-bot/metadata.json
https://mjdavy.github.io/toptastic-bot/latest_playlist.csv
https://mjdavy.github.io/toptastic-bot/songs.csv
```

`songs.db` structure:

- `songs(id, song_name, artist, video_id, video_title, channel_title, video_confidence)`
- `playlists(id, date)` where `date` is yyyymmdd string (Friday chart date)
- `playlist_songs(playlist_id, song_id, position, lw, peak, weeks, is_new, is_reentry)`

### Video Selection Quality

The project uses a heuristic scoring system (see `src/video_selector.py`) to prefer the *official* music video when available and only fall back to lyric / audio / live / cover / remix uploads if necessary. For each song we:

1. Query the YouTube Data API for up to 15 candidate videos (artist + song).
2. Fetch rich metadata (snippet, statistics, contentDetails) for all candidates in a single batch.
3. Assign scores with weighted signals:
    - Strong positives: artist channel match, VEVO channel, presence of "Official Music Video" keywords, good title token overlap, Music category, plausible duration, higher view counts.
    - Penalties: lyric video, audio-only, visualizer, static image, live performance, cover, unrelated remix (unless original title includes remix), out-of-range duration.
4. Persist the highest-scoring candidate.

Additional columns:

- `video_title` – Title chosen for traceability / debugging.
- `channel_title` – Channel of the selected video.
- `video_confidence` – Final heuristic score (higher is better, rough scale ~0–120+). Use this to flag low-confidence matches.

The heuristic is intentionally transparent and easily tunable; adjust the weight constants or add new rules in `video_selector.py` as music metadata patterns evolve.

#### Manual Analysis / Re-evaluation

Use the helper script to inspect the top N songs and see alternative candidate rankings (without modifying the DB):

```bash
python scripts/analyze_top_videos.py --limit 10
```

To target a specific chart date (yyyymmdd) and apply higher-confidence improvements automatically:

```bash
python scripts/analyze_top_videos.py --date 20250926 --limit 15 --min-score 40 --apply
```

Flags:

- `--limit` – number of top positions to analyze (default 10)
- `--date` – chart date; defaults to latest present in DB
- `--apply` – actually persist improved matches
- `--min-score` – require at least this heuristic score before replacing existing mapping

The script prints top 5 candidate videos (with reasons) for quick visual inspection.

## Integrity Verification

Download and verify hash (macOS/Linux):

```bash
curl -L -o songs.db https://mjdavy.github.io/toptastic-bot/songs.db
curl -L -o songs.sha256 https://mjdavy.github.io/toptastic-bot/songs.sha256
[ "$(shasum -a 256 songs.db | cut -d ' ' -f1)" = "$(cat songs.sha256)" ] && echo OK || echo MISMATCH
```

Python example:

```python
import hashlib, requests
BASE = "https://mjdavy.github.io/toptastic-bot"
db_bytes = requests.get(f"{BASE}/songs.db", timeout=30).content
expected = requests.get(f"{BASE}/songs.sha256", timeout=30).text.strip()
actual = hashlib.sha256(db_bytes).hexdigest()
if actual != expected:
    raise SystemExit(f"Hash mismatch: {actual} != {expected}")
open("songs.db", "wb").write(db_bytes)
```

`timestamp.txt` contains the UTC time the file was generated. `metadata.json` includes size, sha256, and schema summary for programmatic consumption.

### CSV Exports

`latest_playlist.csv` columns:

| column | description |
|--------|-------------|
| chart_date | yyyymmdd Friday chart date |
| position | Position on chart (1..N) |
| song_name | Song title |
| artist | Artist name |
| lw | Last week position (0 if new/re-entry) |
| peak | Peak position |
| weeks | Total weeks on chart |
| is_new | 1 if new entry this week |
| is_reentry | 1 if re-entry this week |
| video_id | YouTube video id (may be empty) |
| video_title | Stored video title (may be NULL) |
| channel_title | Channel title (may be NULL) |
| video_confidence | Heuristic score (float, may be NULL) |

`songs.csv` columns:

| column | description |
|--------|-------------|
| id | Internal song id |
| song_name | Song title |
| artist | Artist name |
| video_id | YouTube video id (may be empty) |
| video_title | Stored video title (may be NULL) |
| channel_title | Channel title (may be NULL) |
| video_confidence | Heuristic score (float, may be NULL) |

## Workflows

| Workflow | File | Purpose |
|----------|------|---------|
| Update Songs Database | `.github/workflows/update-database.yml` | Internal run to build/update local DB (no longer commits db) |
| Publish Songs DB (Pages) | `.github/workflows/publish-pages.yml` | Builds, hashes, and deploys artifacts to GitHub Pages |

The *publish* workflow is the source of truth for public artifacts.

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/update_charts.py --mode latest
YOUTUBE_API_KEYS=key1,key2 python scripts/update_videos.py
```

### Makefile Shortcuts

After creating the venv you can also:

```bash
make venv           # create virtual environment
source .venv/bin/activate
make install        # install dependencies
export YOUTUBE_API_KEYS=key1,key2
make update-charts  # scrape latest chart
make update-videos  # enrich video metadata
make analyze        # analyze top 10 candidates
make test           # run tests
```

## Environment Variables

`YOUTUBE_API_KEYS` – Comma-separated list of YouTube Data API keys. The workflow injects this from repository secrets; never commit keys.

## Data Source & Disclaimer

- Chart data is scraped from the public Official Charts website. Song titles, artist names, and chart metrics are factual metadata.
- Respect the source's Terms of Use; this project is for educational/archival purposes and is not affiliated with Official Charts or YouTube.
- YouTube video IDs are public identifiers returned by the YouTube Data API.

## Potential Improvements

- Historical backfill workflow to regenerate older weeks.
- More advanced fuzzy matching (e.g., Levenshtein / token set ratio via RapidFuzz) if false positives persist.
- Channel verification using YouTube channel sections / topic categories.
- Cache per-artist channel IDs to bias future selections.
- Use YouTube Music API (if/when public) or MusicBrainz / ISRC linking for canonical matching.
- Optional GPG-signed hash file for stronger provenance.

## License & Legal

Distributed under the MIT License. See `LICENSE` for full text.

Additional usage / data source notes are in `DISCLAIMER.md`.

---
Questions / ideas? Open an issue (if/when the repo is public) or adapt this README after forking.
