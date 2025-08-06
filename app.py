import logging
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

# Configuración de logs
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Token de Telegram desde variable de entorno
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ¡Hola! Soy el bot de Árbitro FEXB.\n\n"
        "Usa /preguntar para dudas o /informes para redactar informes."
    )

# /preguntar
async def preguntar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("HAS PREGUNTADO")
    await update.message.reply_text("🔍 ¿Qué duda tienes sobre el reglamento?")

# /informes
async def informes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("INFORMES")
    await update.message.reply_text("📝 Vamos a redactar un informe.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("preguntar", preguntar))
    app.add_handler(CommandHandler("informes", informes))

    logging.info("Bot en marcha...")
    app.run_polling()

if __name__ == "__main__":
    main()
