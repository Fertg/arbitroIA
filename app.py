import os
import logging
import requests
import threading
from flask import Flask
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings, StorageContext, load_index_from_storage

# === CARGA VARIABLES ENTORNO ===
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

# === LOGGING ===
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# === CONFIGURACIÓN LLAMA INDEX ===
Settings.embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    cache_folder="./hf_model"
)
Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=20)
Settings.num_output = 512
Settings.context_window = 3900

# === CARGA O CREACIÓN DE ÍNDICE ===
def cargar_o_crear_indice(nombre: str, filtro: str):
    persist_dir = f"storage/{nombre}"
    if os.path.exists(persist_dir):
        logger.info(f"🔁 Cargando índice desde {persist_dir}")
        storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
        return load_index_from_storage(storage_context)
    else:
        logger.info(f"📄 Generando índice para {nombre}")
        documentos = SimpleDirectoryReader(
            "data",
            required_exts=[".pdf"],
            filename_as_id=True,
            recursive=True
        ).load_data(lambda fn: filtro in fn.lower())
        index = VectorStoreIndex.from_documents(documentos, persist_dir=persist_dir)
        index.storage_context.persist()
        return index

# === ÍNDICES ===
index_reglamento = cargar_o_crear_indice("reglamento", filtro="reglas")
query_engine_reglamento = index_reglamento.as_query_engine()

index_informes = cargar_o_crear_indice("informes", filtro="informes")
query_engine_informes = index_informes.as_query_engine()

# === CONSULTA A HUGGING FACE ===
def consulta_huggingface_llm(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    url = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
    body = {"inputs": prompt}

    response = requests.post(url, headers=headers, json=body)
    if response.status_code == 200:
        result = response.json()
        return result[0]["generated_text"] if isinstance(result, list) else result.get("generated_text", "⚠️ Respuesta vacía.")
    else:
        logger.error(f"❌ Error HF: {response.status_code} - {response.text}")
        return "❌ Error al consultar Hugging Face"

# === HANDLERS DE TELEGRAM ===
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

# === INICIO DEL BOT ===
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("preguntar", preguntar))
    app.add_handler(CommandHandler("informes", informes))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("🤖 Bot Árbitro FEXB en marcha...")
    app.run_polling()

# === FLASK PARA RAILWAY ===
flask_app = Flask(__name__)

@flask_app.route("/")
def healthcheck():
    return "✅ Árbitro FEXB en ejecución", 200

# === INICIO APP PRINCIPAL ===
if __name__ == "__main__":
    bot_thread = threading.Thread(target=main)
    bot_thread.start()
    flask_app.run(host="0.0.0.0", port=8080)
