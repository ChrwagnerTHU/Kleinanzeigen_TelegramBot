import json

def get_telegram_token(prod):
    with open("helper/token_config.json", "r") as file:
        data = json.load(file)
        if prod:
            return data[0]["TOKEN"]
        else: 
            return data[0]["TOKEN_DEV"]