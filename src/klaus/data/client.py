import pytz
import os
import logging

from google.cloud import firestore
from datetime import datetime


TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "America/Sao_Paulo"))

# logging configuration
_ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
logging.basicConfig(level=logging.DEBUG if _ENVIRONMENT == "dev" else logging.INFO)
logger = logging.getLogger(__name__)

def get_firestore_client():

    emulator = os.getenv("FIRESTORE_EMULATOR_HOST")
    
    if emulator:
        os.environ.setdefault("GCLOUD_PROJECT", os.getenv("DB_PROJECT_ID"))
        logger.warning(f"⚠️ {datetime.now(TIMEZONE).strftime('%H:%M:%S')} - Using firestore emulator")
        return firestore.Client()
    
    return firestore.Client(project=os.getenv("DB_PROJECT_ID"), database=os.getenv("DB_NAME"))