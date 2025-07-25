import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from llama_index import GPTVectorStoreIndex, SimpleDirectoryReader

# === CARGAR TOKENS DESDE VARIABLES DE ENTORNO ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.1"

# === CONFIGURAR LOGS ===
logging.basicConfig(level=logging.INFO)

# === CARGAR E INDEXAR DOCUMENTOS ===
documents = SimpleDirectoryReader("data").load_data()
index = GPTVectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()

# === FUNCIÓN DE RESPUESTA AL USUARIO ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pregunta = update.message.text
    contexto = query_engine.query(pregunta)

    prompt = f"""Responde según este reglamento:\n{contexto}\n\nPregunta: {pregunta}"""

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
        respuesta = f"Error IA ({response.status_code})"

    await update.message.reply_text(respuesta)

# === INICIAR BOT ===
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot funcionando correctamente.")
    app.run_polling()

if __name__ == '__main__':
    main()
