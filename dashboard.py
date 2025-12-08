import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.graph_objects as go
import os
import yfinance as yf
import numpy as np

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Value Investing Dashboard", layout="wide")
# --- 2. CSS STABILISÉ (Pour la lisibilité) ---
st.markdown("""
    <style>
    /* Augmentation globale de la police */
    html, body, [class*="css"]  {
        font-size: 110% !important; 
    }
    
    /* --- MODIFICATION POUR LE TEST DEV --- */
    /* Tous les titres en ROUGE */
    h1 { 
        font-size: 3rem !important; 
        color: red !important; 
    }
    h2 { 
        font-size: 2.2rem !important; 
        color: red !important; 
    }
    h3 { 
        font-size: 1.8rem !important; 
        color: red !important; 
    }
    /* ------------------------------------ */

    /* Métriques */
    [data-testid="stMetricValue"] {
        font-size: 40px !important; 
    }
    
    /* Espacement */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
    }
    
    /* Inputs */
    .stSlider, .stSelectbox, .stRadio, .stNumberInput {
        margin-bottom: 20px;
    }
    
    /* Cartes */
    .stat-box { 
        border-top: 3px solid #ddd; 
        padding-top: 10px; 
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONNEXION BDD ---
db_url = os.environ.get("DATABASE_URL")
# Fallback pour test local si la variable n'existe pas (A RETIRER EN PROD)
if not db_url:
    # Mettez ici votre URL locale si besoin pour tester
    # db_url = "postgresql://admin:pass@localhost:5432/finance"
    st.error("⚠️ Variable DATABASE_URL manquante.")
    st.stop()

engine = create_engine(db_url)

# --- 4. FONCTIONS DE CALCUL ---
def load_data():
    try:
        query = "SELECT * FROM fundamentals ORDER BY \"Date\" DESC"
        df = pd.read_sql(query, engine)
        return df
    except Exception:
        return pd.DataFrame()

def calculate_dcf(fcf_start, growth_rate_1_5, growth_rate_terminal, discount_rate, shares, net_debt):
    future_fcf = []
    # Projection 5 ans
    for i in range(1, 6):
        fcf = fcf_start * ((1 + growth_rate_1_5 / 100) ** i)
        future_fcf.append(fcf)
        
    # Valeur Terminale
    fcf_year_5 = future_fcf[-1]
    terminal_value = (fcf_year_5 * (1 + growth_rate_terminal / 100)) / ((discount_rate - growth_rate_terminal) / 100)
    
    # Actualisation
    dcf_value = 0
    for i, fcf in enumerate(future_fcf):
        dcf_value += fcf / ((1 + discount_rate / 100) ** (i + 1))
        
    pv_terminal_value = terminal_value / ((1 + discount_rate / 100) ** 5)
    enterprise_value = dcf_value + pv_terminal_value
    equity_value = enterprise_value - net_debt
    fair_value_per_share = equity_value / shares
    
    return fair_value_per_share, future_fcf

def add_styled_trace(fig, x, y, name, color):
    fig.add_trace(go.Scatter(
        x=x, y=y, name=name,
        mode='lines+markers',
        line=dict(width=3, color=color),
        marker=dict(size=9, color='white', line=dict(width=2, color=color))
    ))

# --- 5. APPLICATION PRINCIPALE ---
st.title("Value Investing Dashboard")

df = load_data()

if df.empty:
    st.warning("Aucune donnée. Vérifiez le script ETL.")
else:
    # --- SIDEBAR ---
    st.sidebar.header("Paramètres")
    tickers = df['Ticker'].unique()
    selected_ticker = st.sidebar.selectbox("Société", tickers)
    
    st.sidebar.divider()
    
    unit_choice = st.sidebar.radio("Unités :", ('Milliers (k)', 'Millions (M)', 'Milliards (B)'), index=1)
    
    if unit_choice == 'Milliers (k)':
        divider = 1000; unit_label = "k"
    elif unit_choice == 'Millions (M)':
        divider = 1_000_000; unit_label = "M"
    else:
        divider = 1_000_000_000; unit_label = "B"

    # --- PRÉPARATION DONNÉES ---
    company_data = df[df['Ticker'] == selected_ticker].copy()
    company_data['Date'] = pd.to_datetime(company_data['Date'])
    company_data = company_data.sort_values(by='Date')
    
    # Benchmark
    latest_data_universe = df.sort_values('Date').groupby('Ticker').tail(1)
    avg_net_margin = latest_data_universe['Net_Margin'].mean()
    avg_roce = latest_data_universe['ROCE'].mean()
    
    # Prix Live
    current_price = 0.0; currency = ""
    try:
        ticker_obj = yf.Ticker(selected_ticker)
        info = ticker_obj.fast_info
        current_price = info.last_price
        currency = info.currency
    except:
        current_price = 0; currency = "?"

    last_row = company_data.iloc[-1]
    shares = last_row['Shares_Outstanding']
    net_debt = last_row['Total_Debt'] - last_row['Cash_And_Equiv']
    
    # --- PARTIE 1 : KPI (HAUT DE PAGE) ---
    st.subheader(f"Performance ({len(latest_data_universe)} sociétés)")
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    
    kpi1.metric(f"Prix ({currency})", f"{current_price:.2f}")
    
    eps = last_row['Net_Income'] / shares if shares > 0 else 0
    pe_ratio = current_price / eps if eps > 0 else 0
    kpi2.metric("P/E Ratio", f"{pe_ratio:.1f}x" if pe_ratio > 0 else "N/A")

    kpi3.metric("Marge Nette", f"{last_row['Net_Margin']:.1f}%", delta=f"{last_row['Net_Margin'] - avg_net_margin:.1f}%")
    kpi4.metric("ROCE", f"{last_row['ROCE']:.1f}%", delta=f"{last_row['ROCE'] - avg_roce:.1f}%")
    
    ebitda = last_row['EBIT'] # Proxy
    leverage = net_debt / ebitda if ebitda > 0 else 0
    kpi5.metric("Dette/EBIT", f"{leverage:.2f}x" if leverage > 0 else "Cash", delta_color="inverse")

    st.divider()

    # --- PARTIE 2 : CALCULATEUR DCF (MILIEU) ---
    dcf_possible = False
    fcf_input_raw = 0
    growth_5y = 0
    discount_rate = 0
    terminal_growth = 0
    
    with st.expander(" Calculateur de Juste Valeur (DCF)", expanded=True):
        c_dcf1, c_dcf2 = st.columns([1, 2])
        
        with c_dcf1:
            last_fcf_scaled = last_row['FCF'] / divider
            fcf_input_scaled = st.number_input(f"FCF départ ({unit_label})", value=float(last_fcf_scaled))
            fcf_input_raw = fcf_input_scaled * divider
            
            growth_5y = st.slider("Croissance 5 ans (%)", -5.0, 25.0, 5.0, 0.5)
            discount_rate = st.slider("WACC / Taux (%)", 6.0, 15.0, 10.0, 0.5)
            terminal_growth = st.slider("Croissance Perpétuelle (%)", 0.0, 4.0, 2.0, 0.5)

        with c_dcf2:
            if fcf_input_raw > 0:
                dcf_possible = True
                fair_value, _ = calculate_dcf(fcf_input_raw, growth_5y, terminal_growth, discount_rate, shares, net_debt)
                
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = fair_value,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': f"Juste Valeur ({currency})"},
                    delta = {'reference': current_price, 'relative': True},
                    gauge = {
                        'axis': {'range': [min(current_price, fair_value)*0.5, max(current_price, fair_value)*1.5]},
                        'bar': {'color': "#2E86C1"},
                        'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': current_price}
                    }
                ))
                fig.update_layout(height=280, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("FCF négatif, impossible.")

    st.divider()

    # --- PARTIE 3 : TABLEAU HISTORIQUE (MILIEU-BAS) ---
    st.subheader(f"Historique ({unit_label} {currency})")
    
    cols = ['Date', 'Revenue', 'Net_Income', 'FCF', 'Total_Debt', 'Cash_And_Equiv', 'Shares_Outstanding', 'Revenue_Growth_YoY', 'Net_Margin', 'ROE', 'ROCE']
    disp = company_data[cols].copy()
    disp['Date'] = disp['Date'].dt.strftime('%Y')
    disp = disp.set_index('Date').sort_index(ascending=False).T.reset_index()
    disp.rename(columns={'index': 'Indicateur'}, inplace=True)
    
    # Formatage simple des chiffres
    st.dataframe(disp, use_container_width=True, hide_index=True)

    st.divider()

# --- PARTIE 4 : GRAPHIQUE ÉVOLUTION (BAS) ---
    st.header("Analyse de Rentabilité (5 ans)")
    
    df_chart = company_data.tail(5).copy()
    # On force le formatage en string pour avoir juste l'année (ex: "2023")
    dates_str = df_chart['Date'].dt.strftime('%Y')

    fig_renta = go.Figure()
    
    # Fonction locale pour le style
    def add_styled_trace(fig, x, y, name, color):
        fig.add_trace(go.Scatter(
            x=x, y=y, name=name,
            mode='lines+markers',
            line=dict(width=3, color=color),
            marker=dict(size=9, color='white', line=dict(width=2, color=color))
        ))

    add_styled_trace(fig_renta, dates_str, df_chart['ROE'], 'ROE', '#FF5A5F')
    add_styled_trace(fig_renta, dates_str, df_chart['ROCE'], 'ROCE', '#2C3E50')
    add_styled_trace(fig_renta, dates_str, df_chart['Net_Margin'], 'Marge Nette', '#00C9A7')
    add_styled_trace(fig_renta, dates_str, df_chart['Revenue_Growth_YoY'], 'Croissance', '#FFC107')

    fig_renta.update_layout(
        height=400, 
        plot_bgcolor='white', 
        paper_bgcolor='white', 
        hovermode="x unified",
        # --- MODIFICATION ICI : COULEUR NOIRE ---
        font=dict(color='black'), # Définit la couleur par défaut du texte en noir
        legend=dict(
            orientation="h", 
            y=-0.2, 
            x=0.5, 
            xanchor="center",
            font=dict(color='black', size=14) # Force la légende en noir et un peu plus grande
        ),
        margin=dict(t=20, b=20, l=20, r=20)
    )
    
    # Configuration Axe X (Années) en NOIR
    fig_renta.update_xaxes(
        showgrid=False, 
        type='category', 
        linecolor='#333',     # Ligne de l'axe plus sombre
        tickfont=dict(color='black', size=14) # Années en noir
    )
    
    # Configuration Axe Y (Valeurs) en NOIR
    fig_renta.update_yaxes(
        showgrid=True, 
        gridcolor='#f4f4f4', 
        zeroline=False,
        tickfont=dict(color='black', size=12) # Chiffres % en noir
    )
    
    st.plotly_chart(fig_renta, use_container_width=True)
    
    # --- Cartes Stats (Juste en dessous) ---
    def get_stats(s): return s.iloc[-1], s.mean()
    c1, c2, c3, c4 = st.columns(4)
    
    def metric_card(col, title, val, avg, color):
        # Le titre de la carte est aussi mis en noir avec border-top coloré
        col.markdown(f"<div style='border-top: 3px solid {color}; padding-top:5px; color:black;'><b>{title}</b></div>", unsafe_allow_html=True)
        col.metric("TTM", f"{val:.1f}%", delta=f"{val - avg:.1f}% vs Moy.")

    metric_card(c1, "ROE", *get_stats(df_chart['ROE']), '#FF5A5F')
    metric_card(c2, "ROCE", *get_stats(df_chart['ROCE']), '#2C3E50')
    metric_card(c3, "Marge", *get_stats(df_chart['Net_Margin']), '#00C9A7')
    metric_card(c4, "Croissance", *get_stats(df_chart['Revenue_Growth_YoY']), '#FFC107')

    st.divider()

    # --- PARTIE 5 : TABLEAU SENSIBILITÉ (TOUT EN BAS) ---
    if dcf_possible:
        st.subheader("Analyse de Sensibilité DCF")
        st.caption("Prix de l'action selon WACC (Colonnes) et Croissance Terminale (Lignes)")
        
        # Calcul de la matrice
        rates = [discount_rate - 1, discount_rate, discount_rate + 1]
        growths = [terminal_growth - 0.5, terminal_growth, terminal_growth + 0.5]
        
        matrix = []
        for g in growths:
            row = []
            for r in rates:
                val, _ = calculate_dcf(fcf_input_raw, growth_5y, g, r, shares, net_debt)
                row.append(val)
            matrix.append(row)
            
        sens_df = pd.DataFrame(matrix, index=[f"Gr.{g}%" for g in growths], columns=[f"Tx.{r}%" for r in rates])

        # Configuration : Largeur FIXE en pixels pour éviter le "medium" flou
        # use_container_width=False pour ne pas étirer
        st.dataframe(
            sens_df.style.format("{:.2f}"), 
            use_container_width=False, 
            width=600  # Largeur totale du widget forcée pour rester compact
        )

# Bouton update
if st.sidebar.button('Update Data'):
    os.system("python etl.py")
    st.rerun()