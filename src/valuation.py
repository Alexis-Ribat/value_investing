def calculate_dcf(fcf, g5, gt, wacc, shares, net_debt):
    """Calculates Fair Value per share using Discounted Cash Flow."""
    if shares == 0: return 0
    
    future_fcf = []
    # Project 5 years
    for i in range(1, 6):
        val = fcf * ((1 + g5/100)**i)
        future_fcf.append(val)
        
    # Terminal Value
    fcf_year_5 = future_fcf[-1]
    # Gordon Shapiro for Terminal Value
    terminal_val = (fcf_year_5 * (1 + gt/100)) / ((wacc - gt)/100) if (wacc > gt) else 0
    
    # Discounting
    dcf_sum = 0
    for i, val in enumerate(future_fcf):
        dcf_sum += val / ((1 + wacc/100)**(i+1))
        
    pv_terminal = terminal_val / ((1 + wacc/100)**5)
    enterprise_value = dcf_sum + pv_terminal
    equity_value = enterprise_value - net_debt
    
    return equity_value / shares
    
    
 # ... (laissez la fonction calculate_dcf existante au dessus) ...

def calculate_piotroski_f_score(df):
    """
    Calculates the Piotroski F-Score (0-9) based on financial data.
    """
    if df is None or len(df) < 2: return 0, {}
    
    # We compare TTM (Last row) vs Previous Year (2nd to last)
    ttm = df.iloc[-1]
    prev = df.iloc[-2]
    
    score = 0
    details = {}

    # --- 1. PROFITABILITY ---
    # ROA > 0
    roa = ttm['Net_Income'] / ttm['Total_Equity'] if ttm['Total_Equity'] else 0
    if roa > 0: score += 1; details['Positive ROA'] = True
    else: details['Positive ROA'] = False

    # Positive Operating Cash Flow
    if ttm['Operating_Cash_Flow'] > 0: score += 1; details['Positive OCF'] = True
    else: details['Positive OCF'] = False

    # Higher ROA (YoY)
    roa_prev = prev['Net_Income'] / prev['Total_Equity'] if prev['Total_Equity'] else 0
    if roa > roa_prev: score += 1; details['ROA Improving'] = True
    else: details['ROA Improving'] = False

    # Quality of Earnings (OCF > Net Income)
    if ttm['Operating_Cash_Flow'] > ttm['Net_Income']: score += 1; details['Quality of Earnings'] = True
    else: details['Quality of Earnings'] = False

    # --- 2. LEVERAGE & LIQUIDITY ---
    # Lower Leverage (Long Term Debt / Equity) - Simplified check on Total Debt variation
    if ttm['Total_Debt'] < prev['Total_Debt']: score += 1; details['Debt Decreasing'] = True
    else: details['Debt Decreasing'] = False

    # Current Ratio Improving (Approximation via Working Capital if Current Assets missing, else skip)
    # Note: Yahoo data often lacks full Current Assets/Liabilities in simple view. 
    # We'll use Shares Dilution as a proxy for financial discipline here to keep it robust.
    
    # No Dilution (Shares Outstanding)
    if ttm['Shares_Outstanding'] <= prev['Shares_Outstanding']: score += 1; details['No Dilution'] = True
    else: details['No Dilution'] = False

    # --- 3. OPERATING EFFICIENCY ---
    # Higher Gross Margin (Approximation: We check Net Margin improvement if Gross is unavailable)
    if ttm['Net_Margin'] > prev['Net_Margin']: score += 1; details['Margin Improving'] = True
    else: details['Margin Improving'] = False

    # Asset Turnover (Revenue / Total Assets) - We use Revenue growth as proxy for demand
    if ttm['Revenue'] > prev['Revenue']: score += 1; details['Revenue Growing'] = True
    else: details['Revenue Growing'] = False
    
    # Bonus point to reach 9 (Standard Piotroski has 9 points)
    # We check if FCF is positive
    if ttm['FCF'] > 0: score += 1; details['Positive FCF'] = True
    else: details['Positive FCF'] = False

    return score, details
    
    
# Dans src/valuation.py

def calculate_reverse_dcf(current_price, fcf, gt, wacc, shares, net_debt):
    """
    Reverse DCF: Trouve le taux de croissance (g) implicite pour égaler le prix actuel.
    Retourne un pourcentage (ex: 12.5).
    """
    if current_price <= 0 or shares == 0: return 0
    
    # Bornes de recherche : de -50% à +100% de croissance annuelle
    low = -50.0 
    high = 100.0
    tolerance = 0.1 # On veut une précision à 0.1$ près
    
    for _ in range(100): # 100 itérations max pour éviter boucle infinie
        mid = (low + high) / 2
        # On utilise votre fonction existante pour tester cette croissance 'mid'
        estimated_value = calculate_dcf(fcf, mid, gt, wacc, shares, net_debt)
        
        diff = estimated_value - current_price
        
        if abs(diff) < tolerance:
            return mid
        
        if estimated_value > current_price:
            # Si valeur trop haute -> la croissance testée est trop haute
            high = mid
        else:
            # Si valeur trop basse -> la croissance testée est trop basse
            low = mid
            
    return (low + high) / 2