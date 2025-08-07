FROM python:3.10-slim

WORKDIR /app

# Instala dependencias del sistema
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Instala pip y torch con soporte CPU desde PyTorch oficial
RUN pip install --upgrade pip \
 && pip install torch==2.2.2+cpu -f https://download.pytorch.org/whl/torch_stable.html

# Copia el resto y el requirements.txt
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "app.py"]
