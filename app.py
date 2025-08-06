import os
import logging
import requests
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from llama_index import GPTVectorStoreIndex, SimpleDirectoryReader
from llama_index.llms import MockLLM
from llama_index.embeddings import HuggingFaceEmbedding
from llama_index.service_context import ServiceContext

# === CONFIGURACIÓN ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = "google/flan-t5-base"

# === LOGS ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# === CARGA DE DOCUMENTOS ===
documents = SimpleDirectoryReader("data").load_data()

# === EMBEDDING LOCAL + LLM Mock ===
embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
service_context = ServiceContext.from_defaults(llm=MockLLM(), embed_model=embed_model)
index = GPTVectorStoreIndex.from_documents(documents, service_context=service_context)
query_engine = index.as_query_engine()

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ¡Hola! Soy el bot de Árbitro FEXB.\n\n"
        "🟠 Puedes preguntarme sobre:\n"
        "- Reglamentos de baloncesto\n"
        "- Interpretaciones técnicas\n"
        "- Cómo redactar informes\n\n"
        "❓ Escribe tu duda y te ayudaré."
    )

# === RESPONDER MENSAJES ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pregunta = update.message.text
    contexto = query_engine.query(pregunta)

    prompt = (
        f"Responde a la siguiente pregunta basándote únicamente en este reglamento:\n\n"
        f"{contexto}\n\n"
        f"Pregunta: {pregunta}"
    )

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

    print(f"🔍 Llamando a HF: {url}")
    print(f"🔍 Prompt:\n{prompt}")

    try:
        response = requests.post(
            url,
            headers=headers,
            json={"inputs": prompt},
            timeout=20
        )
        print(f"🔁 STATUS: {response.status_code}")
        print(f"🔁 RESPONSE: {response.text}")

        if response.status_code == 200:
            result = response.json()
            respuesta = result[0]['generated_text'] if isinstance(result, list) else result.get('generated_text', 'Sin respuesta.')
        else:
            respuesta = f"⚠️ Error con la IA ({response.status_code})"
    except Exception as e:
        respuesta = f"❌ Error al conectar con Hugging Face: {e}"

    await update.message.reply_text(respuesta)


# === MAIN ===
def main():
    try:
        app: Application = ApplicationBuilder().token(TELEGRAM_TOKEN).connect_timeout(20).read_timeout(20).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        print("🤖 Árbitro FEXB Bot en marcha...")
        app.run_polling()
    except Exception as e:
        print(f"❌ Error al iniciar el bot: {e}")

if __name__ == '__main__':
    main()
