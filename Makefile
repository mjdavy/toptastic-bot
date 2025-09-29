PYTHON ?= python3
VENV_DIR := .venv
ACTIVATE := . $(VENV_DIR)/bin/activate
REQ := requirements.txt

.PHONY: help venv install update-charts update-videos analyze test lint clean

help:
	@echo 'Common targets:'
	@echo '  make venv            - create virtual environment'
	@echo '  make install         - install dependencies into venv'
	@echo '  make update-charts   - scrape latest chart into DB'
	@echo '  make update-videos   - enrich songs with video metadata'
	@echo '  make analyze         - analyze top 10 videos (set YOUTUBE_API_KEYS first)'
	@echo '  make test            - run pytest suite'
	@echo '  make clean           - remove caches'

venv:
	$(PYTHON) -m venv $(VENV_DIR)
	@echo 'Run: source $(VENV_DIR)/bin/activate'

install: venv
	$(ACTIVATE); pip install --upgrade pip
	$(ACTIVATE); pip install -r $(REQ)

update-charts:
	$(ACTIVATE); python scripts/update_charts.py --mode latest

update-videos:
	@if [ -z "$$YOUTUBE_API_KEYS" ]; then echo 'YOUTUBE_API_KEYS not set'; exit 1; fi
	$(ACTIVATE); python scripts/update_videos.py

analyze:
	@if [ -z "$$YOUTUBE_API_KEYS" ]; then echo 'YOUTUBE_API_KEYS not set'; exit 1; fi
	$(ACTIVATE); python scripts/analyze_top_videos.py --limit 10

# run all tests
test:
	$(ACTIVATE); pytest -q

clean:
	find . -name '__pycache__' -prune -exec rm -rf {} +
	find . -name '*.pyc' -delete
