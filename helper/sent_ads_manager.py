import os
import json

SENT_DIR = "sent_ids"

def sent_pfad(user_id):
    os.makedirs(SENT_DIR, exist_ok=True)
    return os.path.join(SENT_DIR, f"{user_id}.json")

def get_gesendete_ids(user_id):
    pfad = sent_pfad(user_id)
    if not os.path.exists(pfad):
        return set()
    try:
        with open(pfad, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except:
        return set()

def speichere_gesendete_ids(user_id, ids):
    pfad = sent_pfad(user_id)
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(list(ids), f)

def add_gesendete_ids(user_id, neue_ids):
    bekannte = get_gesendete_ids(user_id)
    bekannte.update(neue_ids)
    speichere_gesendete_ids(user_id, bekannte)
