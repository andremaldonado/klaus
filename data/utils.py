import os

from google.cloud import firestore

def get_firestore_client():
    return firestore.Client(project=os.getenv("DB_PROJECT_ID"), database=os.getenv("DB_NAME"))