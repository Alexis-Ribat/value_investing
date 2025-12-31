import yfinance as yf
import pandas as pd
import numpy as np
import requests

def get_safe_val(df, keys):
    for k in keys:
        if k in df.index: return df.loc[k]
    return 0

def fetch_live_data(ticker):
    print(f"DEBUG: Downloading LIVE data for {ticker}...")
    try:
        stock = yf.Ticker(ticker)
        bs, is_, cf = stock.balance_sheet, stock.financials, stock.cashflow
        if is_.empty: return None

        df = pd.DataFrame(index=is_.columns)
        
        # P&L
        df['Revenue'] = get_safe_val(is_, ['Total Revenue', 'TotalRevenue', 'Revenue'])
        df['Net_Income'] = get_safe_val(is_, ['Net Income', 'NetIncome', 'Net Income Common Stockholders'])
        df['EBIT'] = get_safe_val(is_, ['EBIT', 'Operating Income', 'OperatingIncome'])
        
        # Cash Flow
        df['Operating_Cash_Flow'] = get_safe_val(cf, ['Operating Cash Flow', 'Total Cash From Operating Activities'])
        df['CapEx'] = get_safe_val(cf, ['Capital Expenditure', 'Capital Expenditures'])
        
        # Balance Sheet
        df['Total_Debt'] = get_safe_val(bs, ['Total Debt', 'TotalDebt', 'Long Term Debt And Capital Lease Obligation']) 
        if df['Total_Debt'].sum() == 0:
             df['Total_Debt'] = get_safe_val(bs, ['Long Term Debt']) + get_safe_val(bs, ['Current Debt'])

        df['Cash_And_Equiv'] = get_safe_val(bs, ['Cash And Cash Equivalents', 'Cash', 'CashFinancial'])
        df['Total_Equity'] = get_safe_val(bs, ['Stockholders Equity', 'Total Equity Gross Minority Interest'])
        
        df['Shares_Outstanding'] = get_safe_val(bs, ['Share Issued', 'Ordinary Shares Number'])
        if df['Shares_Outstanding'].iloc[0] == 0:
            try: df['Shares_Outstanding'] = stock.info.get('sharesOutstanding', 0)
            except: pass

        # Computed Metrics
        df = df.sort_index()
        df['Revenue_Growth_YoY'] = df['Revenue'].pct_change() * 100
        df['FCF'] = df['Operating_Cash_Flow'] + df['CapEx']
        df['Net_Margin'] = np.where(df['Revenue'] != 0, (df['Net_Income'] / df['Revenue'] * 100), 0)
        df['ROE'] = np.where(df['Total_Equity'] != 0, (df['Net_Income'] / df['Total_Equity'] * 100), 0)
        
        net_debt = df['Total_Debt'] - df['Cash_And_Equiv']
        capital_employed = df['Total_Equity'] + net_debt
        df['ROCE'] = np.where(capital_employed != 0, (df['EBIT'] / capital_employed * 100), 0)

        df['Date'] = df.index
        return df

    except Exception as e:
        print(f"DEBUG: Data Error: {e}")
        return None

def search_yahoo_candidates(query):
    if not query or len(query) < 2: return []
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=3&newsCount=0"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=2)
        data = r.json()
        results = []
        if 'quotes' in data:
            for x in data['quotes']:
                if x.get('quoteType') in ['EQUITY', 'ETF', 'MUTUALFUND']:
                    results.append({'label': f"{x.get('shortname')} ({x['symbol']})", 'symbol': x['symbol'], 'name': x.get('shortname')})
        return results
    except: return []