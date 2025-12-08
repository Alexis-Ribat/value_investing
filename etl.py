import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine
import os

# On force l'utilisation de la variable d'environnement.
# Si elle n'existe pas, cela lèvera une erreur explicite, ce qui est mieux niveau sécurité.
db_url = os.environ.get("DATABASE_URL")

if not db_url:
    raise ValueError("❌ La variable d'environnement DATABASE_URL est manquante.")

engine = create_engine(db_url)

# --- LISTE DES TICKERS ---
# Note : Pour les actions françaises, ajoute ".PA" à la fin.
# MC.PA = LVMH, TTE.PA = TotalEnergies, AI.PA = Air Liquide, OR.PA = L'Oréal
TICKERS = ["AAPL", "MSFT", "GOOGL", "MC.PA", "TTE.PA", "AI.PA", "OR.PA"]

def get_fundamental_data(ticker):
    print(f"Traitement de {ticker}...")
    try:
        stock = yf.Ticker(ticker)
        
        # Récupération des états financiers annuels
        bs = stock.balance_sheet          # Bilan
        is_ = stock.financials            # Compte de résultat
        cf = stock.cashflow               # Flux de trésorerie
        
        # Si les données sont vides, on passe
        if is_.empty or bs.empty:
            print(f"⚠️ Pas de données trouvées pour {ticker} (Vérifiez le ticker sur Yahoo Finance)")
            return None

        # Transposition pour avoir les dates en index (lignes)
        df = pd.DataFrame(index=is_.columns)
        
        # --- EXTRACTION DES MÉTRIQUES BRUTES ---
        # Utilisation de .get() pour éviter les crashs si une ligne manque
        
        # Compte de résultat
        df['Revenue'] = is_.loc['Total Revenue']
        df['Net_Income'] = is_.loc['Net Income']
        
        # EBIT : On essaie plusieurs noms car Yahoo change parfois les labels
        if 'EBIT' in is_.index:
            df['EBIT'] = is_.loc['EBIT']
        elif 'Operating Income' in is_.index:
            df['EBIT'] = is_.loc['Operating Income']
        else:
            df['EBIT'] = 0
        
        # Cash Flow
        df['Operating_Cash_Flow'] = cf.loc['Operating Cash Flow'] if 'Operating Cash Flow' in cf.index else 0
        df['CapEx'] = cf.loc['Capital Expenditure'] if 'Capital Expenditure' in cf.index else 0
        
        # Stock Based Compensation
        df['SBC'] = cf.loc['Stock Based Compensation'] if 'Stock Based Compensation' in cf.index else 0
            
        # Bilan
        df['Total_Assets'] = bs.loc['Total Assets'] if 'Total Assets' in bs.index else 0
        df['Total_Equity'] = bs.loc['Stockholders Equity'] if 'Stockholders Equity' in bs.index else 0
        df['Total_Debt'] = bs.loc['Total Debt'] if 'Total Debt' in bs.index else 0
        df['Cash_And_Equiv'] = bs.loc['Cash And Cash Equivalents'] if 'Cash And Cash Equivalents' in bs.index else 0
        
        # Nombre d'actions (Info actuelle car l'historique est dur à avoir gratuitement)
        df['Shares_Outstanding'] = stock.info.get('sharesOutstanding', 0) 
        
    except Exception as e:
        print(f"Erreur lors de l'extraction pour {ticker}: {e}")
        return None

    # --- CALCUL DES RATIOS VALUE ---
    
    # 1. Croissance CA (Année N vs N-1)
    # CORRECTION ICI : Ajout de fill_method=None pour éviter le Warning
    df['Revenue_Growth_YoY'] = df['Revenue'].pct_change(periods=-1, fill_method=None) * 100
    
    # 2. Free Cash Flow
    df['FCF'] = df['Operating_Cash_Flow'] + df['CapEx']
    
    # 3. Marge Nette
    df['Net_Margin'] = (df['Net_Income'] / df['Revenue']) * 100
    
    # 4. ROE
    df['ROE'] = (df['Net_Income'] / df['Total_Equity']) * 100
    
    # 5. ROCE = EBIT / (Equity + Net Debt)
    net_debt = df['Total_Debt'] - df['Cash_And_Equiv']
    capital_employed = df['Total_Equity'] + net_debt
    # Évite la division par zéro
    df['ROCE'] = df.apply(lambda x: (x['EBIT'] / capital_employed.loc[x.name] * 100) if capital_employed.loc[x.name] != 0 else 0, axis=1)
    
    df['Ticker'] = ticker
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'Date'}, inplace=True)
    
    return df

def run_etl():
    all_data = []
    print("--- Démarrage de la mise à jour ---")
    for t in TICKERS:
        data = get_fundamental_data(t)
        if data is not None:
            all_data.append(data)
    
    if all_data:
        final_df = pd.concat(all_data)
        # Sauvegarde dans PostgreSQL
        try:
            final_df.to_sql('fundamentals', engine, if_exists='replace', index=False)
            print("✅ Base de données mise à jour avec succès !")
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde en base : {e}")
    else:
        print("⚠️ Aucune donnée récupérée.")

if __name__ == "__main__":
    run_etl()