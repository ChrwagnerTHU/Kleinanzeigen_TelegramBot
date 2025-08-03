from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters
from helper.config_manager import add_auftrag
from telegram import Update
from telegram.ext import ContextTypes

FIELDS = [
    "suche", "ort", "preis_max", "versand", "preis_min", "umkreis", "vb"
]

FRAGEN = {
    "suche": "🔍 Was möchtest du suchen?",
    "ort": "📍 In welcher Stadt soll gesucht werden?",
    "preis_max": "📏 Maximaler Preis? (oder 'nein')",
    "versand": "📦 Versand möglich? (ja/nein/egal)",
    "preis_min": "💶 Mindestpreis? (oder 'nein')",
    "umkreis": "🎯 Umkreis in km? (oder 'nein')",
    "vb": "💬 VB erlaubt? (ja/nein/egal)"
}

def parse_wert(feld, eingabe):
    if feld in ["preis_min", "preis_max", "umkreis"]:
        if eingabe.isdigit():
            return int(eingabe)
        elif eingabe == "nein":
            return None
        else:
            return "INVALID"
    if feld in ["versand", "vb"]:
        if eingabe in ["ja", "nein"]:
            return eingabe == "ja"
        elif eingabe == "egal":
            return None
        else:
            return "INVALID"
    return eingabe if eingabe != "nein" else None

async def start_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["auftrag"] = {}
    context.user_data["zustand"] = 0
    feld = FIELDS[0]
    await update.message.reply_text(FRAGEN[feld])
    return 0

async def eingabe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    zustand = context.user_data.get("zustand", 0)
    auftrag = context.user_data.get("auftrag", {})
    user_id = update.effective_user.id

    feld = FIELDS[zustand]
    wert = parse_wert(feld, text)

    if wert == "INVALID":
        await update.message.reply_text(f"⚠️ Ungültige Eingabe. Bitte erneut:\n{FRAGEN[feld]}")
        return zustand

    auftrag[feld] = wert
    context.user_data["auftrag"] = auftrag

    zustand += 1
    context.user_data["zustand"] = zustand

    if zustand >= len(FIELDS):
        if auftrag.get("preis_min") and auftrag.get("preis_max") and auftrag["preis_min"] > auftrag["preis_max"]:
            await update.message.reply_text("⚠️ Mindestpreis > Maximalpreis. Bitte /add neu starten.")
            return ConversationHandler.END

        add_auftrag(user_id, auftrag)
        await update.message.reply_text("✅ Deine Suche wurde gespeichert!")
        return ConversationHandler.END

    await update.message.reply_text(FRAGEN[FIELDS[zustand]])
    return zustand

async def abbrechen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Vorgang abgebrochen.")
    return ConversationHandler.END

FRAGEN = FRAGEN
FIELDS = FIELDS
parse_wert = parse_wert
