FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install torch==2.2.2+cpu -f https://download.pytorch.org/whl/torch_stable.html && \
    pip install -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "app.py"]
