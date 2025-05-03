#!/usr/bin/env python3
import logging
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.youtube import update_video_ids

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("youtube.log", mode="w"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Update video IDs for songs in the database."""
    logger.info("Starting YouTube video ID update process")
    update_video_ids()
    logger.info("YouTube video ID update process completed")

if __name__ == "__main__":
    main()