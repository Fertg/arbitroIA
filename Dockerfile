FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

# Instalar torch desde repo oficial de PyTorch con soporte CPU
RUN pip install --upgrade pip && \
    pip install torch==2.2.2+cpu torchvision==0.17.2+cpu -f https://download.pytorch.org/whl/torch_stable.html && \
    pip install -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "app.py"]
