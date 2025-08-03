# Kleinanzeigen TelegramBot

Ein Telegram-Bot, der eBay Kleinanzeigen durchsucht und neue Anzeigen direkt per Telegram meldet.

## Funktionen
- Suchaufträge mit `/add` anlegen (Suchbegriff, Ort, Preisgrenzen, Versandoptionen, Umkreis, VB).
- Aufträge verwalten: `/list`, `/remove <nr>`, `/edit <nr>` und manuell suchen mit `/search <nr>`.
- Tägliche automatische Suche um 18:30 Uhr.
- Vermeidung doppelter Benachrichtigungen.

## Installation
1. Repository klonen.
2. Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```
3. Telegram‑Bot‑Token in `helper/token_config.json` eintragen (`TOKEN` bzw. `TOKEN_DEV`).
4. Bot starten:
   ```bash
   python main.py
   ```

## Projektstruktur
- `main.py` – setzt Command-Handler, startet Scheduler und Bot.
- `conversation.py` – Dialog zum Anlegen und Bearbeiten von Suchaufträgen.
- `scraper.py` – ruft die Kleinanzeigen-Webseite ab und filtert Ergebnisse.
- `cron_suche.py` – führt gespeicherte Suchen aus und versendet Ergebnisse.
- `notifier.py` – versendet Nachrichten über die Telegram API.
- `helper/` – Verwaltung von Konfigurationen, Tokens und gesendeten Anzeigen.

`configs/` enthält pro Nutzer eine JSON-Datei mit seinen Suchaufträgen. In `sent_ids/` werden bereits gesendete Anzeigen gespeichert, damit keine Duplikate verschickt werden.

## Nutzung
1. Bot in Telegram starten und `/start` aufrufen.
2. Mit `/add` interaktiv eine Suche anlegen.
3. Weitere Befehle mit `/help` anzeigen lassen.
4. Ergebnisse werden automatisch täglich versendet oder bei Bedarf mit `/search <nr>` sofort abgefragt.

## Entwicklung
Tests (sofern vorhanden) können mit `pytest` ausgeführt werden:
```bash
pytest
```
