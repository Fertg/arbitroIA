import os
import logging
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from llama_index.embeddings.huggingface.base import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.llms.mock import MockLLM

# === CARGAR VARIABLES DE ENTORNO ===
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")  # Hugging Face token

# === LOGGING ===
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# === CONFIGURAR LLM y EMBEDDINGS ===
# Settings.llm = MockLLM()  # No usamos LLM interno, lo llamamos por API externa
Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=20)
Settings.num_output = 512
Settings.context_window = 3900

# === FUNCIONES PARA CONSULTAR HUGGING FACE ===
def consulta_huggingface_llm(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    url = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
    body = {
        "inputs": prompt
    }

    response = requests.post(url, headers=headers, json=body)
    if response.status_code == 200:
        result = response.json()
        return result[0]["generated_text"] if isinstance(result, list) else result.get("generated_text", "⚠️ Respuesta vacía.")
    else:
        logger.error(f"Error HF: {response.status_code} - {response.text}")
        return "❌ Error al consultar Hugging Face"

# === CARGAR DOCUMENTOS E INDEXAR ===
documentos_reglamento = SimpleDirectoryReader("data", required_exts=[".pdf"], filename_as_id=True, recursive=True).load_data(
    lambda fn: "reglas" in fn.lower() or "interpretaciones" in fn.lower()
)
index_reglamento = VectorStoreIndex.from_documents(documentos_reglamento)
query_engine_reglamento = index_reglamento.as_query_engine()

documentos_informes = SimpleDirectoryReader("data", required_exts=[".pdf"], filename_as_id=True, recursive=True).load_data(
    lambda fn: "informes" in fn.lower()
)
index_informes = VectorStoreIndex.from_documents(documentos_informes)
query_engine_informes = index_informes.as_query_engine()

# === HANDLERS DE COMANDOS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ¡Hola! Soy Árbitro IA FEXB.\n\n"
        "📚 Usa /preguntar para dudas del reglamento e interpretaciones.\n"
        "📝 Usa /informes para dudas sobre informes."
    )

async def preguntar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("HAS PREGUNTADO")
    context.user_data["modo"] = "preguntar"
    await update.message.reply_text("Escribe tu pregunta sobre reglamento o interpretaciones:")

async def informes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("INFORMES")
    context.user_data["modo"] = "informes"
    await update.message.reply_text("Escribe tu pregunta sobre redacción de informes:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pregunta = update.message.text
    modo = context.user_data.get("modo", "preguntar")

    if modo == "informes":
        contexto = query_engine_informes.query(pregunta)
    else:
        contexto = query_engine_reglamento.query(pregunta)

    prompt = (
        f"Responde a la siguiente pregunta basándote únicamente en este contenido:\n\n"
        f"{contexto}\n\n"
        f"Pregunta: {pregunta}"
    )

    respuesta = consulta_huggingface_llm(prompt)
    await update.message.reply_text(respuesta)

# === MAIN ===
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("preguntar", preguntar))
    app.add_handler(CommandHandler("informes", informes))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("🤖 Bot Árbitro FEXB en marcha...")
    app.run_polling()

if __name__ == '__main__':
    main()
