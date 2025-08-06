import os
import logging
import openai
from telegram import Update
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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

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
        "👋 ¡Hola! Soy el bot de Árbitro FEXB (con OpenAI).\n\n"
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

    print("🔍 Llamando a OpenAI")
    print(f"🔍 Prompt:\n{prompt}")

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un experto en reglas de baloncesto FIBA."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=500,
        )
        respuesta = completion['choices'][0]['message']['content']
    except Exception as e:
        print(f"❌ Error al conectar con OpenAI: {e}")
        respuesta = "⚠️ Error al contactar con OpenAI."

    await update.message.reply_text(respuesta)

# === MAIN ===
def main():
    try:
        app: Application = ApplicationBuilder().token(TELEGRAM_TOKEN).connect_timeout(20).read_timeout(20).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        print("🤖 Árbitro FEXB Bot con OpenAI en marcha...")
        app.run_polling()
    except Exception as e:
        print(f"❌ Error al iniciar el bot: {e}")

if __name__ == '__main__':
    main()
