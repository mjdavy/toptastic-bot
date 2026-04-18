UV ?= uv
VENV_DIR := .venv

.PHONY: help venv install lock update-charts update-videos analyze test clean

help:
	@echo 'Common targets:'
	@echo '  make venv            - create uv virtual environment'
	@echo '  make install         - sync dependencies with uv'
	@echo '  make lock            - refresh uv lockfile'
	@echo '  make update-charts   - scrape latest chart into DB'
	@echo '  make update-videos   - enrich songs with video metadata'
	@echo '  make analyze         - analyze top 10 videos (set YOUTUBE_API_KEYS first)'
	@echo '  make test            - run pytest suite'
	@echo '  make clean           - remove caches'

venv:
	$(UV) venv $(VENV_DIR)
	@echo 'Run commands with $(UV) run ... or activate $(VENV_DIR) if needed'

install:
	$(UV) sync

lock:
	$(UV) lock

update-charts:
	$(UV) run python scripts/update_charts.py --mode latest

update-videos:
	@if [ -z "$$YOUTUBE_API_KEYS" ]; then echo 'YOUTUBE_API_KEYS not set'; exit 1; fi
	$(UV) run python scripts/update_videos.py

analyze:
	@if [ -z "$$YOUTUBE_API_KEYS" ]; then echo 'YOUTUBE_API_KEYS not set'; exit 1; fi
	$(UV) run python scripts/analyze_top_videos.py --limit 10

# run all tests
test:
	$(UV) run pytest -q

clean:
	find . -name '__pycache__' -prune -exec rm -rf {} +
	find . -name '*.pyc' -delete
