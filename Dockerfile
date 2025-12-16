FROM python:3.11-slim

WORKDIR /app

# --- 1. SYSTÈME (Cache très fort) ---
RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    build-essential \
    curl \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# --- 2. PYTHON LIBS (Cache fort - 90 secondes économisées) ---
# On le fait AVANT Rust. Comme ça, si on change Rust, on ne réinstalle pas Pandas.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# --- 3. MOTEUR RUST (Cache moyen - 70 secondes) ---
COPY rust_engine ./rust_engine

RUN cd rust_engine && \
    cargo build --release && \
    mv target/release/edgar_fetcher /usr/local/bin/edgar_fetcher && \
    chmod +x /usr/local/bin/edgar_fetcher

# --- 4. LE RESTE (Code Python) ---
# En réalité, cette étape est écrasée par le volume docker-compose au runtime,
# mais on la garde pour la propreté de l'image finale.
COPY . .

CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]