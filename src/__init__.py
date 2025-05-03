# toptastic-bot package
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("toptastic.log", mode="w"),
        logging.StreamHandler()
    ]
)