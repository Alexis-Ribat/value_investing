# 📈 Value Investing Dashboard

A comprehensive **Streamlit-based web application** for fundamental stock analysis and value investing research. This platform combines financial data from multiple sources with AI-powered insights to help investors make informed decisions using proven value investing methodologies (Warren Buffett / Terry Smith style).

## ✨ Features

### 📊 Core Functionality

- **Stock Search & Data Fetching**
  - Search by company name or ticker symbol
  - AI-assisted ticker resolution using Google Gemini
  - Support for US and international stocks (e.g., LVMH, JNBY)
  - Real-time data from Yahoo Finance

- **Financial Analysis**
  - **DCF Valuation Calculator**: Fair value estimation with customizable assumptions
  - **Piotroski F-Score**: 9-point fundamental strength assessment
  - **Key Metrics**: P/E, ROCE, Debt/EBIT, ROE, margins, and more
  - **SEC Data Integration**: Official SEC EDGAR filings via Rust-powered engine
  - **Trend Analysis**: 5+ years of revenue, earnings, and cash flow trends

- **Governance & Ownership**
  - Ownership breakdown (Insiders, Institutions, Public Float)
  - Top 5 institutional holders
  - Insider roster with positions

- **AI-Powered Insights**
  - Company profile summaries
  - Revenue segmentation analysis
  - Earnings sentiment analysis (news scanning)
  - Full investment thesis generation using custom prompts

- **Data Storage**
  - PostgreSQL database for caching AI reports
  - Session state management for seamless user experience

## 🏗 Architecture

The project uses a **hybrid architecture** combining Python for business logic and Rust for performance-critical data processing:

- **Frontend**: Streamlit (Python) web interface
- **AI Engine**: Google Gemini API with key rotation support
- **Data Sources**: 
  - Yahoo Finance (yfinance) for market data
  - SEC EDGAR (via Rust fetcher) for official filings
- **Database**: PostgreSQL for data persistence
- **Performance**: Rust engine for SEC data fetching
- **Deployment**: Docker & Docker Compose

## 📂 Project Structure

```
.
├── main.py                    # Streamlit application entry point
├── prompt.txt                 # AI prompt template for investment reports
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker image definition
├── docker-compose.yml         # Multi-container orchestration
│
├── src/                       # Python source code
│   ├── ai_engine.py          # AI integration (Gemini API)
│   ├── data_provider.py      # Yahoo Finance data fetching
│   ├── valuation.py          # DCF, Piotroski F-Score calculations
│   ├── computed_metrics.py   # Value investing metrics (Graham, etc.)
│   ├── sec_provider.py       # SEC EDGAR data via Rust engine
│   ├── database.py           # PostgreSQL connection and caching
│   └── ui_components.py      # Chart rendering (Plotly)
│
├── rust_engine/              # Rust performance engine
│   ├── Cargo.toml
│   └── src/
│       └── main.rs           # SEC EDGAR data fetcher
│
└── logs/                     # Application logs
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- `.env` file with required environment variables (see Configuration)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd value_investing/dev
   ```

2. **Create `.env` file**
   ```env
   ENV_NAME=dev
   HOST_PORT=8501
   DB_PORT=5432
   POSTGRES_USER=your_user
   POSTGRES_PASSWORD=your_password
   POSTGRES_DB=value_investing
   DATABASE_URL=postgresql://your_user:your_password@db:5432/value_investing
   GEMINI_API_KEY=your_gemini_api_key
   GEMINI_API_KEY_1=optional_additional_key
   FMP_API_KEY=optional_fmp_key
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Access the dashboard**
   - Open your browser and navigate to `http://localhost:8501`
   - The dashboard should be running and ready to use

### Development Mode

For development with live code reloading:

```bash
docker-compose up
```

The code is mounted as a volume, so changes to Python files will automatically reload in Streamlit.

## 📋 Usage

### Dashboard Tabs

1. **Valuation**
   - DCF fair value calculator with interactive sliders
   - Implied growth calculation
   - Key valuation metrics (P/E, P/B, Graham Number, etc.)
   - Piotroski F-Score details

2. **Management & Capital**
   - Ownership breakdown (Insiders, Institutions, Public Float)
   - Top institutional holders table
   - Insider roster

3. **Trends & Data**
   - Business segments (revenue breakdown)
   - Profitability trends (ROE, ROCE, Net Margin)
   - Financial data tables (5-year history)
   - SEC official data with visual trends

4. **AI Analyst**
   - Latest news sentiment analysis
   - Earnings call transcript analysis
   - AI-powered insights and recommendations

5. **Full Report**
   - Comprehensive investment thesis generator
   - Uses custom prompt template (`prompt.txt`)
   - Downloadable markdown reports
   - Report caching in database

### Searching for Stocks

- Use the sidebar search bar to find companies by name or ticker
- The AI will help resolve company names to ticker symbols if needed
- Favorite stocks are shown by default when no search is active

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ENV_NAME` | Environment identifier | Yes |
| `HOST_PORT` | Port for Streamlit app | Yes |
| `DB_PORT` | PostgreSQL port | Yes |
| `POSTGRES_USER` | Database username | Yes |
| `POSTGRES_PASSWORD` | Database password | Yes |
| `POSTGRES_DB` | Database name | Yes |
| `DATABASE_URL` | Full database connection string | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `GEMINI_API_KEY_1` | Additional Gemini keys (for rotation) | No |
| `FMP_API_KEY` | Financial Modeling Prep API key | No |

### API Keys

- **Google Gemini**: Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- You can add multiple keys (GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.) for automatic rotation when quotas are reached

## 🛠 Technology Stack

- **Python 3.11**: Core application logic
- **Streamlit**: Web framework
- **Rust**: Performance engine for SEC data fetching
- **PostgreSQL 15**: Database
- **Docker**: Containerization
- **Key Libraries**:
  - `yfinance`: Market data
  - `plotly`: Interactive charts
  - `pandas`: Data manipulation
  - `google-generativeai`: AI integration
  - `sqlalchemy`: Database ORM

## 📊 Data Sources

- **Yahoo Finance**: Real-time market data, financial statements, company info
- **SEC EDGAR**: Official regulatory filings (10-K, 10-Q, etc.)
- **Google News**: Financial news for sentiment analysis

## 🔍 Key Metrics Calculated

- **Valuation Metrics**: DCF, Graham Number, P/E, P/B, EV/EBITDA, P/FCF
- **Profitability**: ROE, ROCE, Net Margin, Operating Margin
- **Financial Health**: Debt/EBIT, Current Ratio, Cash Position
- **Quality Scores**: Piotroski F-Score (0-9)

## 🤖 AI Features

- **Ticker Resolution**: AI-powered company name to ticker symbol conversion
- **Company Profiles**: Automated business model and competitive analysis
- **Revenue Segmentation**: AI-estimated revenue breakdown by segment
- **Sentiment Analysis**: News and earnings call sentiment evaluation
- **Investment Reports**: Comprehensive investment thesis generation

## 📝 Notes

- The application caches AI responses in the database to minimize API costs
- SEC data is fetched using a Rust engine for improved performance
- Some features (like SEC data) are limited to US stocks
- The dashboard supports both US and international stock exchanges

## 🐛 Troubleshooting

### No Data Showing

- Verify your `.env` file is correctly configured
- Check that Docker containers are running: `docker-compose ps`
- Review logs: `docker-compose logs dashboard`

### API Errors

- Ensure your Gemini API key is valid and has quota remaining
- Check for rate limiting messages in the logs
- Consider adding additional API keys for rotation

### Database Connection Issues

- Verify PostgreSQL container is running: `docker-compose ps db`
- Check database credentials in `.env`
- Ensure `DATABASE_URL` format is correct

## 🙏 Acknowledgments

- Built for value investors following Warren Buffett and Terry Smith methodologies
- Uses data from Yahoo Finance and SEC EDGAR
- Powered by Google Gemini AI

---

**Happy Investing! 📈**
