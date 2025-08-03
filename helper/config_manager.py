import json
import os
from pathlib import Path

CONFIG_DIR = "configs"

def config_pfad(user_id):
    return os.path.join(CONFIG_DIR, f"{user_id}.json")

def lade_config(user_id):
    path = config_pfad(user_id)
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def speichere_config(user_id, config):
    path = config_pfad(user_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def list_auftraege(user_id):
    return lade_config(user_id)

def add_auftrag(user_id, auftrag):
    daten = lade_config(user_id)
    daten.append(auftrag)
    speichere_config(user_id, daten)

def remove_auftrag(user_id, index):
    daten = lade_config(user_id)
    if 0 <= index < len(daten):
        daten.pop(index)
        speichere_config(user_id, daten)
        return True
    return False

def edit_auftrag(user_id, index, neues_dict):
    daten = lade_config(user_id)
    if 0 <= index < len(daten):
        daten[index].update(neues_dict)
        speichere_config(user_id, daten)
        return True
    return False