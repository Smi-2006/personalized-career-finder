import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Load Firebase key from environment variable
firebase_key = os.environ.get("FIREBASE_KEY")

if not firebase_key:
    raise ValueError("FIREBASE_KEY environment variable not set")

key_dict = json.loads(firebase_key)

cred = credentials.Certificate(key_dict)
firebase_admin.initialize_app(cred)

db = firestore.client()
