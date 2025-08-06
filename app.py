# app.py
import os
import logging
from telegram import Update
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters)
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
from dotenv import load_dotenv

# === CONFIGURACIÓN ===
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# === LOGS ===
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# === CONFIG GLOBAL LLAMAINDEX ===
Settings.llm = OpenAI(api_key=OPENAI_API_KEY, model="gpt-3.5-turbo")
Settings.embed_model = OpenAIEmbedding(api_key=OPENAI_API_KEY, model="text-embedding-3-small")
Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=20)
Settings.num_output = 512
Settings.context_window = 3900

# === INDEXACIÓN DE DOCUMENTOS ===
documentos_reglamento = SimpleDirectoryReader(
    "data", required_exts=[".pdf"], filename_as_id=True, recursive=True
).load_data(lambda fn: "reglas" in fn.lower() or "interpretaciones" in fn.lower())
index_reglamento = VectorStoreIndex.from_documents(documentos_reglamento)
query_engine_reglamento = index_reglamento.as_query_engine()

documentos_informes = SimpleDirectoryReader(
    "data", required_exts=[".pdf"], filename_as_id=True, recursive=True
).load_data(lambda fn: "informes" in fn.lower())
index_informes = VectorStoreIndex.from_documents(documentos_informes)
query_engine_informes = index_informes.as_query_engine()

# === COMANDOS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ¡Hola! Soy Árbitro IA FEXB.\n\n"
        "📚 Usa /preguntar para dudas del reglamento e interpretaciones.\n"
        "📝 Usa /informes para dudas sobre informes."
    )

async def preguntar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("HAS PREGUNTADO")
    await update.message.reply_text("Escribe tu pregunta sobre reglamento o interpretaciones:")
    context.user_data["modo"] = "preguntar"

async def informes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("INFORMES")
    await update.message.reply_text("Escribe tu pregunta sobre redacción de informes:")
    context.user_data["modo"] = "informes"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pregunta = update.message.text
    modo = context.user_data.get("modo")

    if modo == "informes":
        respuesta = query_engine_informes.query(pregunta)
    else:
        respuesta = query_engine_reglamento.query(pregunta)

    await update.message.reply_text(str(respuesta))

# === MAIN ===
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("preguntar", preguntar))
    app.add_handler(CommandHandler("informes", informes))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("🤖 Bot en marcha...")
    app.run_polling()

if __name__ == '__main__':
    main()
