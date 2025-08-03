from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
)
from cron_suche import suche_task
from helper.config_manager import (
    list_auftraege,
    remove_auftrag,
    edit_auftrag,
)
from conversation import start_add, eingabe, abbrechen, FIELDS, FRAGEN, parse_wert
from helper.token_helper import get_telegram_token
from scraper import suche_anzeigen
from notifier import sende_telegram_nachricht

import logging
import schedule
import asyncio


# Telegram Zugangsdaten
TELEGRAM_BOT_TOKEN=get_telegram_token(True)

# Logging aktivieren (optional)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ───────────────────────────────────────────────────────────────
# 🔁 Standardbefehle
# ───────────────────────────────────────────────────────────────

async def start(update, context):
    await update.message.reply_text(
        "👋 Willkommen! Nutze folgende Befehle:\n"
        "/add – Neue Suche starten\n"
        "/list – Aktuelle Suchaufträge anzeigen\n"
        "/remove – Suche löschen (/remove 1)\n"
        "/edit – Suche bearbeiten (/edit 1)\n"
        "/cancel – Vorgang abbrechen"
    )


async def help_command(update, context):
    await update.message.reply_text(
        "📖 <b>Verfügbare Kommandos</b>:\n\n"
        "/start – Begrüßung & Schnellhilfe\n"
        "/help – Diese Hilfe anzeigen\n"
        "/add – Neue Suche interaktiv anlegen\n"
        "/list – Alle aktiven Suchaufträge anzeigen\n"
        "/remove &lt;Zahl&gt; – Auftrag löschen (z. B. /remove 1)\n"
        "/edit &lt;Zahl&gt; – Auftrag bearbeiten (z. B. /edit 1)\n"
        "/cancel – Vorgang abbrechen",
        parse_mode="HTML"
    )


async def list_suchen(update, context):
    user_id = update.effective_user.id
    auftraege = list_auftraege(user_id)

    if not auftraege:
        await update.message.reply_text("📭 Keine gespeicherten Suchaufträge.")
        return

    msg = "\n\n".join([
        f"{idx + 1}. 🔍 <b>{a['suche']}</b> in {a.get('ort', '–')}, max. {a.get('preis_max', '∞')} €"
        for idx, a in enumerate(auftraege)
    ])
    await update.message.reply_text(f"📋 Deine Suchaufträge:\n\n{msg}", parse_mode="HTML")


async def remove_suche(update, context):
    user_id = update.effective_user.id
    try:
        index = int(update.message.text.replace("/remove", "").strip()) - 1
        erfolg = remove_auftrag(user_id, index)
        if erfolg:
            await update.message.reply_text("🗑️ Suche erfolgreich entfernt.")
        else:
            await update.message.reply_text("⚠️ Ungültiger Index.")
    except:
        await update.message.reply_text("⚠️ Nutzung: /remove INDEX")

async def manuelle_suche(update, context):
    user_id = update.effective_user.id
    try:
        index = int(update.message.text.replace("/search", "").strip()) - 1
        auftraege = list_auftraege(user_id)
        if not (0 <= index < len(auftraege)):
            await update.message.reply_text("⚠️ Ungültiger Index.")
            return

        auftrag = auftraege[index]
        await update.message.reply_text("🔄 Suche wird ausgeführt...")

        ergebnisse = suche_anzeigen(auftrag, user_id)

        if not ergebnisse:
            await update.message.reply_text("📭 Keine Anzeigen gefunden.")
            return

        await sende_telegram_nachricht(
            auftrag_config=auftrag,
            chat_id=user_id,
            anzeigen=ergebnisse,
            user_id=user_id
        )

    except Exception as e:
        print(f"[manuelle_suche Fehler] {e}")
        await update.message.reply_text("⚠️ Nutzung: /search INDEX")

# ───────────────────────────────────────────────────────────────
# ✏️ Edit-Modus (ConversationHandler)
# ───────────────────────────────────────────────────────────────

async def edit_suche(update, context):
    user_id = update.effective_user.id
    try:
        index = int(update.message.text.replace("/edit", "").strip()) - 1
        auftraege = list_auftraege(user_id)
        if not (0 <= index < len(auftraege)):
            await update.message.reply_text("⚠️ Ungültiger Index.")
            return ConversationHandler.END

        context.user_data["bearbeiten"] = {
            "index": index,
            "auftrag": auftraege[index],
            "zustand": 0,
            "user_id": user_id
        }

        feld = FIELDS[0]
        await update.message.reply_text(f"✏️ Bitte neuen Wert für:\n{FRAGEN[feld]}")
        return 0

    except Exception as e:
        await update.message.reply_text("⚠️ Nutzung: /edit INDEX")
        logger.warning(f"/edit Fehler: {e}")
        return ConversationHandler.END


async def bearbeite_eingabe(update, context):
    text = update.message.text.strip().lower()
    daten = context.user_data.get("bearbeiten")
    if not daten:
        await update.message.reply_text("⚠️ Bearbeitungsdaten fehlen. Bitte /edit neu starten.")
        return ConversationHandler.END

    zustand = daten["zustand"]
    feld = FIELDS[zustand]
    wert = parse_wert(feld, text)

    if wert == "INVALID":
        await update.message.reply_text(f"⚠️ Ungültige Eingabe. Bitte erneut:\n{FRAGEN[feld]}")
        return zustand

    daten["auftrag"][feld] = wert
    daten["zustand"] += 1

    if daten["zustand"] >= len(FIELDS):
        erfolg = edit_auftrag(daten["user_id"], daten["index"], daten["auftrag"])
        if erfolg:
            await update.message.reply_text("✅ Auftrag erfolgreich bearbeitet!")
        else:
            await update.message.reply_text("❌ Fehler beim Bearbeiten.")
        return ConversationHandler.END

    next_feld = FIELDS[daten["zustand"]]
    await update.message.reply_text(f"➡️ Weiter: {FRAGEN[next_feld]}")
    return daten["zustand"]

# ───────────────────────────────────────────────────────────────
#  Scheduler
# ───────────────────────────────────────────────────────────────
def schedule_jobs(application):
    async def job():
        await suche_task()

    async def scheduler():
        schedule.every().day.at("18:30").do(lambda: asyncio.create_task(job()))
        while True:
            schedule.run_pending()
            await asyncio.sleep(30)

    asyncio.create_task(scheduler())

async def post_init(application):
    schedule_jobs(application)


# ───────────────────────────────────────────────────────────────
# 🏁 Main-Funktion
# ───────────────────────────────────────────────────────────────

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    # ConversationHandler für /add
    add_handler = ConversationHandler(
        entry_points=[CommandHandler("add", start_add)],
        states={
            i: [MessageHandler(filters.TEXT & ~filters.COMMAND, eingabe)]
            for i in range(len(FIELDS))
        },
        fallbacks=[CommandHandler("cancel", abbrechen)],
    )

    # ConversationHandler für /edit
    edit_handler = ConversationHandler(
        entry_points=[CommandHandler("edit", edit_suche)],
        states={
            i: [MessageHandler(filters.TEXT & ~filters.COMMAND, bearbeite_eingabe)]
            for i in range(len(FIELDS))
        },
        fallbacks=[CommandHandler("cancel", abbrechen)],
    )

    # Standard-Handler
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("list", list_suchen))
    app.add_handler(CommandHandler("remove", remove_suche))
    app.add_handler(CommandHandler("search", manuelle_suche))
    app.add_handler(add_handler)
    app.add_handler(edit_handler)

    # Bot starten
    app.run_polling()

if __name__ == "__main__":
    main()
