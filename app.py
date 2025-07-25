import os
import logging
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# LlamaIndex
from llama_index import GPTVectorStoreIndex, SimpleDirectoryReader
from llama_index.llms import MockLLM
from llama_index.embeddings import HuggingFaceEmbedding
from llama_index.service_context import ServiceContext

# === CONFIGURACIÓN ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.1"

# === LOGS ===
logging.basicConfig(level=logging.INFO)

# === CARGA DE DOCUMENTOS ===
documents = SimpleDirectoryReader("data").load_data()

# === USAR IA LOCAL (HuggingFace) y evitar OpenAI ===
embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/paraphrase-MiniLM-L3-v2")
service_context = ServiceContext.from_defaults(llm=MockLLM(), embed_model=embed_model)

# === INDEXACIÓN ===
index = GPTVectorStoreIndex.from_documents(documents, service_context=service_context)
query_engine = index.as_query_engine()

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = (
        "👋 ¡Hola! Soy el bot de Árbitros FEXB.\n\n"
        "🟠 Puedes preguntarme sobre:\n"
        "- Reglamentos de baloncesto\n"
        "- Interpretaciones técnicas\n"
        "- Cómo redactar informes\n\n"
        "❓ Escribe tu duda y te ayudaré."
    )
    await update.message.reply_text(mensaje)

# === RESPUESTA DE IA ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pregunta = update.message.text
    contexto = query_engine.query(pregunta)

    prompt = (
        f"Responde a la siguiente pregunta basándote únicamente en este reglamento:\n\n"
        f"{contexto}\n\n"
        f"Pregunta: {pregunta}"
    )

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    response = requests.post(
        f"https://api-inference.huggingface.co/models/{HF_MODEL}",
        headers=headers,
        json={"inputs": prompt}
    )

    if response.status_code == 200:
        result = response.json()
        respuesta = result[0]['generated_text'] if isinstance(result, list) else result.get('generated_text', 'Sin respuesta.')
    else:
        respuesta = f"⚠️ Error con la IA ({response.status_code})"

    await update.message.reply_text(respuesta)

# === MAIN ===
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Árbitros FEXB Bot en marcha...")
    app.run_polling()

if __name__ == '__main__':
    main()
