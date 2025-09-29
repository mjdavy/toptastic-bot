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

- `songs(id, song_name, artist, video_id)`
- `playlists(id, date)` where `date` is yyyymmdd string (Friday chart date)
- `playlist_songs(playlist_id, song_id, position, lw, peak, weeks, is_new, is_reentry)`

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

`songs.csv` columns:

| column | description |
|--------|-------------|
| id | Internal song id |
| song_name | Song title |
| artist | Artist name |
| video_id | YouTube video id (may be empty) |

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

## Environment Variables

`YOUTUBE_API_KEYS` – Comma-separated list of YouTube Data API keys. The workflow injects this from repository secrets; never commit keys.

## Data Source & Disclaimer

- Chart data is scraped from the public Official Charts website. Song titles, artist names, and chart metrics are factual metadata.
- Respect the source's Terms of Use; this project is for educational/archival purposes and is not affiliated with Official Charts or YouTube.
- YouTube video IDs are public identifiers returned by the YouTube Data API.

## Potential Improvements

- Add historical backfill workflow to regenerate older weeks.
- Provide a CSV export alongside SQLite.
- Add optional GPG-signed hash file for stronger provenance.

## License & Legal

Distributed under the MIT License. See `LICENSE` for full text.

Additional usage / data source notes are in `DISCLAIMER.md`.

---
Questions / ideas? Open an issue (if/when the repo is public) or adapt this README after forking.
