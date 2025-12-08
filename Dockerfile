FROM python:3.9-slim

WORKDIR /app

# Installation des dépendances système pour psycopg2 (driver postgres)
RUN apt-get update && apt-get install -y libpq-dev gcc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Par défaut, on lance Streamlit
CMD ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]