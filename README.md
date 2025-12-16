# 📈 Value Investing AI & Analytics

This project is a high-performance financial analysis platform combining the flexibility of **Python** (for AI and data management) with the speed of **Rust** (for intensive calculations). It is designed to automate fundamental analysis (Value Investing) by aggregating data from multiple sources (SEC, Bloomberg/NAS, FMP).

## 🏗 Hybrid Architecture

The project is built on a modular architecture:

* **Core (Python 3.11):** Orchestration, API connectors (SEC, Data Providers), and the AI Engine (`src/ai_engine.py`).
* **Performance Engine (Rust):** High-performance module for computing financial metrics and heavy data processing (`rust_engine/`).
* **Database:** Data persistence using PostgreSQL.
* **Infrastructure:** Fully containerized via Docker & Docker Compose.

## 📂 Project Structure

```text
.
├── src/                  # Python Source Code (Business Logic)
│   ├── ai_engine.py      # AI Engine for qualitative analysis
│   ├── valuation.py      # Valuation models (DCF, Graham, etc.)
│   ├── sec_provider.py   # Regulators connectors (SEC EDGAR)
│   └── database.py       # Database connection management
├── rust_engine/          # Rust Calculation Engine
├── docker-compose.yml    # Service orchestration
├── Dockerfile            # Main application image
├── requirements.txt      # Python dependencies
└── main.py               # Entry point
