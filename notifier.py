from telegram import Bot

from helper.token_helper import get_telegram_token
from helper.sent_ads_manager import add_gesendete_ids

async def sende_telegram_nachricht(auftrag_config, chat_id, anzeigen, user_id):
    if not anzeigen:
        return

    bot = Bot(token=get_telegram_token(True))
    gesendet = []
    suchbegriff = auftrag_config.get("suche", "")

    param_info = (
        f"\n📍 Ort: <b>{auftrag_config.get('ort', '–')}</b> (Umkreis: {auftrag_config.get('umkreis', '–')} km)"
        f"\n💶 Preis: <b>{auftrag_config.get('preis_min') or '–'} – {auftrag_config.get('preis_max') or '–'} €</b>"
        f"\n📦 Versand: <b>{'Ja' if auftrag_config.get('versand') is True else 'Nein' if auftrag_config.get('versand') is False else 'Egal'}</b>"
        f"\n💬 VB erlaubt: <b>{'Ja' if auftrag_config.get('vb') is True else 'Nein' if auftrag_config.get('vb') is False else 'Egal'}</b>"
    )

    header = f"🔍 <b>Neue Anzeigen für:</b> <i>{suchbegriff}</i>{param_info}\n"
    messages = [header]

    for a in anzeigen:
        msg = (
            f"<b>{a['titel']}</b>\n"
            f"{a['preis']} – {a['ort']}\n"
            f"<a href='{a['link']}'>Zur Anzeige</a>"
        )

        if "bild" in a and a["bild"]:
            try:
                if messages:
                    await bot.send_message(chat_id=chat_id, text=messages[0], parse_mode="HTML")
                    messages = []
                await bot.send_photo(chat_id=chat_id, photo=a["bild"], caption=msg, parse_mode="HTML")
                gesendet.append(a['id'])
                continue
            except Exception as e:
                print(f"[Bildfehler] {e}")

        messages.append(msg)
        gesendet.append(a['id'])

    if messages:
        await bot.send_message(chat_id=chat_id, text="\n\n".join(messages), parse_mode="HTML")
    add_gesendete_ids(user_id, gesendet)