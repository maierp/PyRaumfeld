FROM python:3.9-slim

EXPOSE 8080

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "RaumfeldControl.py"]