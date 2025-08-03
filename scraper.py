import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import random
from geopy.distance import geodesic
from geopy.geocoders import Nominatim

from helper.sent_ads_manager import get_gesendete_ids

# Geocoder für Ort zu Koordinaten
geolocator = Nominatim(user_agent="kleinanzeigen_bot", timeout=10)

def ort_zu_koordinaten(ort_string):
    try:
        location = geolocator.geocode(ort_string)
        if location:
            return (location.latitude, location.longitude)
    except:
        pass
    return None

def entfernung_km(ort1, ort2):
    if ort1 is None or ort2 is None:
        return float("inf")
    return geodesic(ort1, ort2).km

def suche_anzeigen(auftrag, user_id):
    base_url = "https://www.kleinanzeigen.de/s-suchanfrage.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    gesamt_ergebnisse = []

    prev_ergebnisse = get_gesendete_ids(user_id)

    # Prüfe Umkreis und Ort sicher
    umkreis = auftrag.get("umkreis")
    if auftrag.get("ort") and isinstance(umkreis, (int, float)) and umkreis > 0:
        ziel_koord = ort_zu_koordinaten(auftrag["ort"])
    else:
        ziel_koord = None

    params = {
        "keywords": auftrag["suche"]
    }

    if ziel_koord:
        params["locationStr"] = auftrag["ort"]
        params["radius"] = umkreis

    if auftrag.get("preis_min") is not None:
        params["minPrice"] = auftrag["preis_min"]
    if auftrag.get("preis_max") is not None:
        params["maxPrice"] = auftrag["preis_max"]

    url = base_url + "?" + urllib.parse.urlencode(params)

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            print(f"⚠️ HTTP {resp.status_code}")
    except requests.RequestException as e:
        print(f"❌ Anfragefehler")

    soup = BeautifulSoup(resp.text, "html.parser")
    vorher = len(gesamt_ergebnisse)

    for ad in soup.select(".aditem"):
        link_tag = ad.select_one("a[href]")
        if not link_tag:
            continue
        link = "https://www.kleinanzeigen.de" + link_tag["href"]
        ad_id = link.split("/")[-1]

        if (ad_id in prev_ergebnisse):
            continue

        titel = ad.select_one(".text-module-begin .ellipsis")
        titel = titel.text.strip() if titel else "Kein Titel"

        preis_block = ad.select_one(".aditem-main--middle--price-shipping")
        preis = preis_block.text.strip() if preis_block else "Kein Preis"

        beschreibung = ad.select_one(".aditem-main--middle--description")
        beschreibung = beschreibung.text.strip() if beschreibung else ""

        ort = ad.select_one(".aditem-main--top--left")
        ort = ort.text.strip() if ort else "Unbekannt"

        bild_tag = ad.select_one("img")
        bild_url = bild_tag["src"] if bild_tag and "src" in bild_tag.attrs else None

        if ziel_koord:
            ad_koord = ort_zu_koordinaten(ort)
            if ad_koord:
                dist = entfernung_km(ziel_koord, ad_koord)
                if dist > umkreis:
                    continue

        versand_config = auftrag.get("versand")
        if versand_config is True:
            if "Versand möglich" not in ad.get_text():
                continue

        if auftrag.get("vb") is False and "VB" in preis:
            continue

        gesamt_ergebnisse.append({
            "id": ad_id,
            "titel": titel,
            "preis": preis,
            "ort": ort,
            "beschreibung": beschreibung,
            "link": link,
            "bild": bild_url
        })

        if len(gesamt_ergebnisse) == vorher:
            break

        time.sleep(random.uniform(1, 2))

    return gesamt_ergebnisse
