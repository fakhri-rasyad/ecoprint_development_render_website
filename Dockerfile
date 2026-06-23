FROM python:3.12.4-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ENV FASTAPI_DATABASE_URL=postgresql+psycopg2://fastapi_user_url:fastapipass@localhost:5432/ecoprint
# ENV ALEMBIC_DATABASE_URL=postgresql+psycopg2://alembic_user_url:alembicpass@localhost:5432/ecoprint
# ENV MQTT_HOST=localhost
# ENV MQTT_PORT=1883

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]