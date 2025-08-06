import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from llama_index import SimpleDirectoryReader, GPTVectorStoreIndex
from llama_index.llms import OpenAI
from llama_index.embeddings import OpenAIEmbedding
from llama_index.service_context import ServiceContext
from dotenv import load_dotenv

# Cargar variables .env
load_dotenv()

# Configuración
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Logging
logging.basicConfig(level=logging.INFO)

# === IA ===
def cargar_index(ficheros):
    documentos = SimpleDirectoryReader(input_files=ficheros).load_data()
    llm = OpenAI(api_key=OPENAI_API_KEY, model="gpt-3.5-turbo")
    embedding = OpenAIEmbedding(api_key=OPENAI_API_KEY)
    service_context = ServiceContext.from_defaults(llm=llm, embed_model=embedding)
    return GPTVectorStoreIndex.from_documents(documentos, service_context=service_context)

# === HANDLERS ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ¡Hola! Soy el bot de Árbitro FEXB.\n\n"
        "Puedes usar /preguntar para reglamentos e interpretaciones\n"
        "o /informes para dudas sobre informes."
    )

async def preguntar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📘 Has seleccionado *Preguntar*. Escribe tu duda...", parse_mode="Markdown")
    context.user_data["modo"] = "preguntar"

async def informes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 Has seleccionado *Informes*. Escribe tu duda...", parse_mode="Markdown")
    context.user_data["modo"] = "informes"

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pregunta = update.message.text
    modo = context.user_data.get("modo")

    if not modo:
        await update.message.reply_text("❗ Usa /preguntar o /informes antes de escribir.")
        return

    if modo == "preguntar":
        index = cargar_index(["data/reglas.pdf", "data/interpretaciones.pdf"])
    else:
        index = cargar_index(["data/informes.pdf"])

    query_engine = index.as_query_engine()
    respuesta = query_engine.query(pregunta)
    await update.message.reply_text(str(respuesta))

# === MAIN ===
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("preguntar", preguntar))
    app.add_handler(CommandHandler("informes", informes))
    app.add_handler(MessageHandler(~CommandHandler, manejar_mensaje))
    app.run_polling()

if __name__ == "__main__":
    main()
