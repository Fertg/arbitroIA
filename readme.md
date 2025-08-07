# 🏀 Árbitros FES Bot – Normativa Baloncesto con IA

Este bot de Telegram responde preguntas sobre el reglamento de baloncesto FIBA y documentos técnicos gracias a la IA de Llama.

## 📦 Estructura

├── app.py
├── data/ # Aquí van los PDFs y PPTs con normativa
├── requirements.txt
├── Procfile
├── .gitignore


## 🧠 Funcionalidades

- Lee los documentos locales (`informes.pdf`, `interpretaciones.pdf`, `reglas.pdf`)
- Indexa el contenido con LlamaIndex
- Responde preguntas por Telegram usando IA (Mistral vía Hugging Face)

### 🛠️ Requisitos

- Python 3.10+
- Tokens de Telegram y Hugging Face
- Archivos de normativa en `data/`

## ✍️ Autor

Desarrollado por [FerTG](https://github.com/Fertg) para Árbitros FEXB. s
