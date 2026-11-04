FROM python:3.12-slim

WORKDIR /app

COPY app/main.py .

EXPOSE 80

CMD ["python", "main.py"]
