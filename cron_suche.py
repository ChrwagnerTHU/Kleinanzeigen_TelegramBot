import asyncio
import os
import json
from scraper import suche_anzeigen
from notifier import sende_telegram_nachricht
from helper.config_manager import lade_config

CONFIG_DIR = "configs"
SENT_DIR = "sent_ids"

def lade_bekannte_anzeigen(user_id):
    path = os.path.join(SENT_DIR, f"{user_id}.json")
    if not os.path.exists(path):
        return set()
    try:
        with open(path, "r") as f:
            return set(json.load(f))
    except:
        return set()

def speichere_bekannte_anzeigen(user_id, ids):
    os.makedirs(SENT_DIR, exist_ok=True)
    path = os.path.join(SENT_DIR, f"{user_id}.json")
    with open(path, "w") as f:
        json.dump(list(ids), f)

async def suche_task():
    for file in os.listdir(CONFIG_DIR):
        if file.endswith(".json"):
            user_id = file.replace(".json", "")
            auftraege = lade_config(user_id)
            bekannte_ids = lade_bekannte_anzeigen(user_id)

            for auftrag in auftraege:
                neue_anzeigen = []
                ergebnisse = suche_anzeigen(auftrag, user_id)
                for ad in ergebnisse:
                    if ad["id"] not in bekannte_ids:
                        bekannte_ids.add(ad["id"])
                        neue_anzeigen.append(ad)

                await sende_telegram_nachricht(
                    auftrag_config=auftrag,
                    chat_id=user_id,
                    anzeigen=neue_anzeigen,
                    user_id=user_id
                )
            speichere_bekannte_anzeigen(user_id, bekannte_ids)

if __name__ == "__main__":
    asyncio.run(suche_task())
