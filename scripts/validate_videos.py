#!/usr/bin/env python3
"""Check all stored video IDs against the YouTube API and clear stale ones.

Run this before update_videos.py so that deleted/private videos get re-fetched
with a fresh search rather than staying broken in the database indefinitely.
"""
import logging
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.youtube import validate_video_ids

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("youtube.log", mode="w"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting video ID validation")
    cleared = validate_video_ids()
    logger.info(f"Validation complete — {cleared} stale IDs cleared")
    if cleared:
        logger.info("Run update_videos.py to re-fetch videos for cleared entries")
