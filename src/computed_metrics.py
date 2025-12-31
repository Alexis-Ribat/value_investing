import numpy as np
import pandas as pd

def calculate_metrics_from_yahoo(df, info):
    """
    Calcule les métriques 'Value Investing' (Graham, NCAV, Ratios) 
    à partir des données brutes Yahoo (df) et des métadonnées (info).
    Fallback gratuit à FMP.
    """
    if df.empty: return None

    # On prend les dernières données disponibles
    last = df.iloc[-1]
    
    # Données de base (Prix et Actions)
    price = info.get('currentPrice', info.get('regularMarketPreviousClose', 0))
    shares = last.get('Shares_Outstanding', 0)
    
    if price <= 0 or shares <= 0: return None

    # 1. EPS & Book Value
    net_income = last.get('Net_Income', 0)
    equity = last.get('Total_Equity', 0)
    
    eps = net_income / shares
    bvps = equity / shares # Book Value Per Share

    # 2. Graham Number = Sqrt(22.5 * EPS * BVPS)
    graham_number = 0
    if eps > 0 and bvps > 0:
        graham_number = np.sqrt(22.5 * eps * bvps)

    # 3. EV / EBITDA
    mcap = price * shares
    total_debt = last.get('Total_Debt', 0)
    cash = last.get('Cash_And_Equiv', 0)
    enterprise_value = mcap + total_debt - cash
    
    ebitda = last.get('EBIT', 0)
    # Si EBIT manquant dans le DF, on regarde si info l'a
    if ebitda == 0 and 'ebitda' in info: ebitda = info['ebitda']
    
    ev_ebitda = enterprise_value / ebitda if ebitda > 0 else 0

    # 4. Ratios
    pe_ratio = price / eps if eps > 0 else 0
    pb_ratio = price / bvps if bvps > 0 else 0
    
    fcf = last.get('FCF', 0)
    p_fcf = mcap / fcf if fcf > 0 else 0
    
    earnings_yield = (eps / price) if price > 0 else 0
    div_yield = info.get('dividendYield', 0)
    if div_yield is None: div_yield = 0

    return {
        "P/E Ratio": pe_ratio,
        "P/B Ratio": pb_ratio,
        "P/FCF": p_fcf,
        "EV / EBITDA": ev_ebitda,
        "Graham Number": graham_number,
        "Earnings Yield": earnings_yield,
        "Dividend Yield": div_yield,
        "Source": "Yahoo Calculated"
    }