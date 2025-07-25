import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from llama_index import VectorStoreIndex, Document
from document_loader import extraer_texto_pdf, extraer_texto_ppt

# === CONFIG ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.1"

# === LOGGING ===
logging.basicConfig(level=logging.INFO)

# === CARGAR Y INDEXAR DOCUMENTOS ===
def cargar_documentos():
    docs = []
    carpeta = "data"
    for archivo in os.listdir(carpeta):
        ruta = os.path.join(carpeta, archivo)
        if archivo.endswith(".pdf"):
            texto = extraer_texto_pdf(ruta)
        elif archivo.endswith(".pptx"):
            texto = extraer_texto_ppt(ruta)
        else:
            continue
        docs.append(Document(text=texto))
    return VectorStoreIndex.from_documents(docs)

index = cargar_documentos()
query_engine = index.as_query_engine()

# === MANEJADOR DE MENSAJES ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pregunta = update.message.text
    contexto = query_engine.query(pregunta)

    prompt = f"""Contesta basándote únicamente en el siguiente reglamento:\n{contexto}\n\nPregunta: {pregunta}"""

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

# === ARRANCAR BOT ===
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot desplegado.")
    app.run_polling()

if __name__ == '__main__':
    main()
