FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir opencv-python-headless==4.10.0.84

COPY infer.py /app/infer.py

CMD ["python", "/app/infer.py"]
