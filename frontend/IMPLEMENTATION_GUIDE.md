# Implementation Guide: Shareholder Component Integration

This guide explains how to integrate the TypeScript shareholder component with your Python Streamlit backend.

## Architecture Overview

```
┌─────────────────────┐
│  React/TypeScript   │
│  Frontend           │◄──────── ShareholderComponent
│  (port 3000)        │
└──────────┬──────────┘
           │
           │ HTTP Requests
           │ (fetch/axios)
           ▼
┌─────────────────────┐
│  Python Backend     │
│  Streamlit/FastAPI  │◄──────── REST API Endpoints
│  (port 8000)        │
└──────────┬──────────┘
           │
           │ API Calls
           │ (yfinance)
           ▼
┌─────────────────────┐
│  Yahoo Finance API  │
└─────────────────────┘
```

## Option 1: Create Python Backend API (Recommended)

### Step 1: Add FastAPI to Python Backend

```bash
pip install fastapi uvicorn
```

### Step 2: Create `src/api/shareholders.py`

```python
"""
API endpoint for shareholder data
Returns data matching the TypeScript ShareholderData interface
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import yfinance as yf
from datetime import datetime
from typing import Optional, Dict, Any

router = APIRouter(prefix="/api/shareholders", tags=["shareholders"])

CACHE = {}
CACHE_TTL = 86400  # 24 hours


def get_major_holders_breakdown(ticker: str) -> Dict[str, float]:
    """Extract major holders breakdown from Yahoo Finance"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        return {
            "insidersPercent": info.get("heldPercentInsiders", 0),
            "institutionsPercent": info.get("heldPercentInstitutions", 0),
            "floatPercent": 100 - info.get("heldPercentInsiders", 0) - info.get("heldPercentInstitutions", 0),
        }
    except:
        return {
            "insidersPercent": 0,
            "institutionsPercent": 0,
            "floatPercent": 100,
        }


def get_top_institutional_holders(ticker: str) -> list:
    """Extract top institutional holders from Yahoo Finance"""
    try:
        stock = yf.Ticker(ticker)
        
        # Yahoo Finance provides major_holders dataframe
        if hasattr(stock, 'major_holders') and stock.major_holders is not None:
            holders = []
            price = stock.info.get('currentPrice', 0) or stock.info.get('regularMarketPrice', 0)
            
            for idx, row in stock.major_holders.iterrows():
                try:
                    name = row[0]
                    shares = int(row[1].replace(',', '')) if isinstance(row[1], str) else 0
                    pct_held = float(row[2].replace('%', '')) if isinstance(row[2], str) else 0
                    
                    holders.append({
                        "holder": name,
                        "shares": shares,
                        "value": shares * price if price > 0 else 0,
                        "dateReported": datetime.now().isoformat(),
                        "pctHeld": pct_held,
                    })
                except:
                    continue
            
            return holders
        
        return []
    except Exception as e:
        print(f"Error fetching holders for {ticker}: {e}")
        return []


@router.get("/{ticker}")
async def get_shareholders(ticker: str) -> Dict[str, Any]:
    """
    Get shareholder data for a given ticker
    
    Returns:
        {
            "majorHoldersBreakdown": {...},
            "topInstitutionalHolders": [...],
            "currency": "USD",
            "lastUpdated": "2024-01-15T..."
        }
    """
    try:
        # Check cache
        if ticker in CACHE:
            cached_data, timestamp = CACHE[ticker]
            if (datetime.now() - timestamp).total_seconds() < CACHE_TTL:
                return cached_data
        
        # Fetch fresh data
        stock = yf.Ticker(ticker)
        info = stock.info
        
        data = {
            "majorHoldersBreakdown": get_major_holders_breakdown(ticker),
            "topInstitutionalHolders": get_top_institutional_holders(ticker),
            "currency": info.get("currency", "USD"),
            "lastUpdated": datetime.now().isoformat(),
        }
        
        # Cache the result
        CACHE[ticker] = (data, datetime.now())
        
        return data
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch shareholder data: {str(e)}"
        )
```

### Step 3: Add to Main FastAPI App

```python
# In your main.py or app setup

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import shareholders

app = FastAPI()

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(shareholders.router)

# Run with: uvicorn main:app --reload --port 8000
```

## Option 2: Create Node.js Yahoo Finance Service

### Step 1: Setup Node.js Project

```bash
mkdir backend-node
cd backend-node
npm init -y
npm install express yahoo-finance2 cors dotenv
npm install -D typescript @types/node @types/express ts-node-dev
```

### Step 2: Create `src/routes/shareholders.ts`

```typescript
import express, { Router } from 'express';
import { queryQuote } from 'yahoo-finance2/dist/esm/src';

const router = Router();
const cache = new Map<string, { data: any; timestamp: number }>();
const CACHE_TTL = 86400000; // 24 hours

interface ShareholderData {
  majorHoldersBreakdown: {
    insidersPercent: number;
    institutionsPercent: number;
    floatPercent: number;
  };
  topInstitutionalHolders: Array<{
    holder: string;
    shares: number;
    value: number;
    dateReported: string;
    pctHeld: number;
  }>;
  currency: string;
  lastUpdated: string;
}

router.get('/:ticker', async (req, res) => {
  try {
    const { ticker } = req.params;

    // Check cache
    const cached = cache.get(ticker);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      return res.json(cached.data);
    }

    // Fetch from Yahoo Finance
    const quote = await queryQuote({
      modules: [
        'price',
        'quoteType',
        'defaultKeyStatistics',
        'institutionOwnership',
      ],
      symbol: ticker,
    });

    // Transform to ShareholderData format
    const shareholderData: ShareholderData = {
      majorHoldersBreakdown: {
        insidersPercent:
          parseFloat(quote.defaultKeyStatistics?.insidersPercent) || 0,
        institutionsPercent:
          parseFloat(quote.defaultKeyStatistics?.institutionsPercent) || 0,
        floatPercent: 100 - (parseFloat(quote.defaultKeyStatistics?.insidersPercent) || 0) - (parseFloat(quote.defaultKeyStatistics?.institutionsPercent) || 0),
      },
      topInstitutionalHolders: [], // Yahoo Finance doesn't provide this directly
      currency: quote.price?.currency || 'USD',
      lastUpdated: new Date().toISOString(),
    };

    // Cache and return
    cache.set(ticker, { data: shareholderData, timestamp: Date.now() });
    res.json(shareholderData);
  } catch (error) {
    console.error('Error fetching shareholders:', error);
    res.status(500).json({
      error: 'Failed to fetch shareholder data',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

export default router;
```

## Option 3: Update TypeScript Service for Python Backend

### Modify `frontend/services/shareholderService.ts`

```typescript
export async function fetchShareholders(ticker: string): Promise<ShareholderData | null> {
  try {
    // Call Python backend
    const response = await fetch(
      `http://localhost:8000/api/shareholders/${ticker}`
    );
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    return data as ShareholderData;
  } catch (error) {
    console.error(`Failed to fetch shareholder data for ${ticker}:`, error);
    
    // Fallback to mock data in development
    if (process.env.NODE_ENV === 'development') {
      console.warn('Using mock data for development');
      return mockYahooData[ticker] || null;
    }
    
    return null;
  }
}
```

## Step 4: Configure CORS (Important!)

### Python FastAPI

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",    # Next.js dev
        "http://localhost:3001",    # Production frontend
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Node.js Express

```typescript
import cors from 'cors';

app.use(cors({
  origin: ['http://localhost:3000', 'http://localhost:3001'],
  credentials: true,
}));
```

## Step 5: Environment Configuration

### Frontend `.env.local`

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Frontend `shareholderService.ts`

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchShareholders(ticker: string): Promise<ShareholderData | null> {
  const response = await fetch(`${API_BASE_URL}/api/shareholders/${ticker}`);
  return response.json();
}
```

## Testing the Integration

### 1. Start Python Backend

```bash
# Install dependencies
pip install fastapi uvicorn yfinance

# Run server
uvicorn main:app --reload --port 8000
```

### 2. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### 3. Test API Endpoint

```bash
curl http://localhost:8000/api/shareholders/AAPL
```

### 4. Verify in React DevTools

- Open http://localhost:3000
- Select a stock ticker
- Check Network tab for API requests
- Inspect component props in React DevTools

## Troubleshooting

### CORS Errors

**Error**: `Access to XMLHttpRequest blocked by CORS policy`

**Solution**: 
- Verify backend CORS middleware is configured
- Check frontend `API_BASE_URL` environment variable
- Ensure both frontend and backend are running

### 404 Errors

**Error**: `GET /api/shareholders/AAPL 404`

**Solution**:
- Verify endpoint path matches (check typos)
- Ensure router is included in main app
- Check backend is running on correct port

### No Data Returned

**Error**: Component shows "No shareholder data available"

**Solution**:
- Verify ticker symbol is correct
- Check Yahoo Finance has data for that ticker
- Review backend logs for API errors
- Test with `AAPL` or `MC.PA` first

## Production Deployment

### Frontend (Vercel/Netlify)

```bash
# Set environment variable in deployment dashboard
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### Backend (Heroku/Railway)

```bash
# Set environment variable
CORS_ORIGINS=https://yourdomain.com

# Deploy
git push heroku main
```

## Next Steps

1. Choose your preferred API option (FastAPI recommended for Python stack)
2. Implement the API endpoint
3. Update `shareholderService.ts` to call your API
4. Test with multiple tickers
5. Add error handling and retry logic
6. Deploy to production

## Resources

- [Yahoo Finance 2 npm package](https://www.npmjs.com/package/yahoo-finance2)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Express.js Guide](https://expressjs.com/)
- [CORS Documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
