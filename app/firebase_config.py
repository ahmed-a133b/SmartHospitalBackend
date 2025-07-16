import os
import json
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, db

load_dotenv()

def init_firebase():
    json_str = os.getenv("FIREBASE_KEY_JSON")
    db_url = os.getenv("FIREBASE_DATABASE_URL")

    if not json_str or not db_url:
        raise ValueError("Missing FIREBASE_KEY_JSON or FIREBASE_DATABASE_URL")

    try:
        json_data = json.loads(json_str)  
        cred = credentials.Certificate(json_data)  
    except json.JSONDecodeError as e:
        raise ValueError("Invalid FIREBASE_KEY_JSON. Check your .env formatting.") from e

    firebase_admin.initialize_app(cred, {
        'databaseURL': db_url
    })
def get_ref(path: str):
    return db.reference(path)