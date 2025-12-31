import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import os
import requests
from bs4 import BeautifulSoup

# Modular Imports
from src.database import init_db
from src.data_provider import fetch_live_data, search_yahoo_candidates
from src.ai_engine import resolve_ticker_with_ai_cached, get_company_profile_french, generate_ai_insight, get_revenue_split_ai
from src.ui_components import render_profitability_chart, render_revenue_donut, render_governance_component
from src.valuation import calculate_dcf, calculate_piotroski_f_score, calculate_reverse_dcf
from src.sec_provider import get_sec_data_rust
# AJOUTEZ CETTE LIGNE CI-DESSOUS :
from src.computed_metrics import calculate_metrics_from_yahoo

# --- SESSION STATE ---
# ... (vos autres lignes) ...
if 'ai_analysis_result' not in st.session_state: st.session_state.ai_analysis_result = None
if 'full_report_result' not in st.session_state: st.session_state.full_report_result = None # <--- AJOUTER CECI

# --- INIT ---
init_db()
st.set_page_config(page_title="Value Investing Dashboard", layout="wide")

# --- STYLES ---
st.markdown("""
    <style>
    div.stButton > button { width: 100%; text-align: left !important; }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'active_ticker' not in st.session_state: st.session_state.active_ticker = None
if 'active_name' not in st.session_state: st.session_state.active_name = ""
if 'data_cache' not in st.session_state: st.session_state.data_cache = pd.DataFrame()
if 'search_results' not in st.session_state: st.session_state.search_results = []

# --- CALLBACKS ---
def select_ticker_callback(symbol, name):
    if symbol == 'ERR': return
    st.session_state.active_ticker = symbol
    st.session_state.active_name = name
    st.session_state.search_widget = ""
    st.session_state.search_results = []
    
    with st.spinner(f"Loading data for {symbol}..."):
        df = fetch_live_data(symbol)
        st.session_state.data_cache = df if df is not None else pd.DataFrame()

def on_search_change():
    query = st.session_state.search_widget
    if not query: 
        st.session_state.search_results = []
        return

    # 1. Direct Search
    candidates = search_yahoo_candidates(query)
    
    # 2. AI Fallback if empty
    if not candidates:
        ai_ticker = resolve_ticker_with_ai_cached(query)
        if ai_ticker == "ERROR_QUOTA":
            candidates = [{'label': "⚠️ AI Quota Exceeded", 'symbol': 'ERR', 'name': 'Error'}]
        elif ai_ticker:
            candidates = search_yahoo_candidates(ai_ticker)
            
    st.session_state.search_results = candidates

# --- SIDEBAR ---
st.sidebar.header("🔍 Search")

# Widget de recherche
st.sidebar.text_input("Company or Ticker", key="search_widget", on_change=on_search_change)

# Logique d'affichage : Soit Résultats de recherche, Soit Favoris par défaut
results_to_display = []

if st.session_state.search_results:
    st.sidebar.caption("Search Results:")
    results_to_display = st.session_state.search_results
else:
    st.sidebar.caption("⭐ Favorites / Suggestions:")
    # Votre liste personnalisée (J'ai corrigé les tickers pour qu'ils marchent sur Yahoo)
    results_to_display = [
        {'symbol': 'AAPL', 'name': 'Apple Inc.', 'label': '🍎 Apple'},
        {'symbol': 'FTNT', 'name': 'Fortinet Inc.', 'label': '🛡️ Fortinet'},
        {'symbol': 'META', 'name': 'Meta Platforms', 'label': '♾️ Meta'},
        {'symbol': 'ETSY', 'name': 'Etsy, Inc.', 'label': '🧶 Etsy'},
        {'symbol': 'CROX', 'name': 'Crocs, Inc.', 'label': '🐊 Crocs'},
        {'symbol': 'MC.PA', 'name': 'LVMH', 'label': '👜 LVMH (Paris)'},       # Corrigé de LVMA.PA à MC.PA (Ticker Yahoo officiel)
        {'symbol': '3306.HK', 'name': 'JNBY Design', 'label': '👗 JNBY (Hong Kong)'}, # Corrigé pour Yahoo (HK)
        {'symbol': 'NVO', 'name': 'Novo Nordisk', 'label': '💊 Novo Nordisk'}
    ]

# Boucle d'affichage des boutons
for item in results_to_display:
    # On définit un label propre s'il n'existe pas déjà
    label = item.get('label', f"{item['name']} ({item['symbol']})")
    
    # On utilise une clé unique pour éviter les erreurs Streamlit
    # Si c'est un résultat de recherche, item['symbol'] suffit.
    # Si c'est un favori, on préfixe pour être sûr.
    btn_key = f"side_btn_{item['symbol']}"
    
    st.sidebar.button(
        label, 
        key=btn_key, 
        on_click=select_ticker_callback, 
        args=(item['symbol'], item['name'])
    )

# --- MAIN DISPLAY ---
df = st.session_state.data_cache
current_ticker = st.session_state.active_ticker

if df.empty:
    st.info("Please search for a company in the sidebar.")
else:
    # 1. HEADER & METRICS
    st.subheader(f"{st.session_state.active_name} ({current_ticker})")
    
    last = df.iloc[-1]
    avgs = df.mean(numeric_only=True)
    
    # Get Price & Currency
    price, cur = 0.0, "?"
    try: 
        info = yf.Ticker(current_ticker).fast_info
        price = info.last_price
        cur = info.currency
    except: pass
    
    # Metrics Columns
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric(f"Price ({cur})", f"{price:.2f}")
    
    shares = last['Shares_Outstanding']
    pe = price / (last['Net_Income']/shares) if shares > 0 and last['Net_Income'] > 0 else 0
    k2.metric("P/E", f"{pe:.1f}x")
    
    k3.metric("ROCE", f"{last['ROCE']:.1f}%", delta=f"{last['ROCE'] - avgs['ROCE']:.1f}%")
    
    nd = last['Total_Debt'] - last['Cash_And_Equiv']
    lev = nd / last['EBIT'] if last['EBIT'] != 0 else 0
    k4.metric("Debt/EBIT", f"{lev:.1f}x")

    # Piotroski F-Score
    f_score, f_details = calculate_piotroski_f_score(df)
    k5.metric("F-Score", f"{f_score}/9", delta="Strong" if f_score >= 7 else "Weak", delta_color="normal" if f_score >= 7 else "inverse")

    st.markdown("---")

    # 2. COMPANY PROFILE & METADATA (English, No Emojis)
    # We fetch extended info from Yahoo Finance
    stock_info = yf.Ticker(current_ticker)
    info = stock_info.info

    # Market Cap Formatting
    mcap = info.get('marketCap', 0)
    if mcap >= 1e9: mcap_str = f"{mcap / 1e9:.2f} B"
    elif mcap >= 1e6: mcap_str = f"{mcap / 1e6:.2f} M"
    else: mcap_str = f"{mcap}"

    # Safe ISIN retrieval
    isin = getattr(stock_info, 'isin', 'N/A')
    if not isin: isin = "N/A"

    # Row 1
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f"**Sector:** {info.get('sector', 'N/A')}")
    m2.markdown(f"**Industry:** {info.get('industry', 'N/A')}")
    m3.markdown(f"**Country:** {info.get('country', 'N/A')}")
    m4.markdown(f"**Exchange:** {info.get('exchange', 'N/A')}")

    # Row 2
    m5, m6, m7, m8 = st.columns(4)
    m5.markdown(f"**Market Cap:** {mcap_str}")
    m6.markdown(f"**Currency:** {info.get('currency', 'N/A')}")
    m7.markdown(f"**ISIN:** {isin}")
    m8.markdown(f"**Employees:** {info.get('fullTimeEmployees', 'N/A')}")

    # Text Description (Still fetched in French via AI as per previous logic, but displayed cleanly)
    summary = get_company_profile_french(current_ticker, st.session_state.active_name)
    if summary:
        st.markdown("### 🧠 Strategic Analysis")
        # On utilise un conteneur pour encadrer proprement l'analyse
        with st.container(border=True):
            st.markdown(summary)
    
    st.divider()

    # --- TABS ORGANIZATION ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Valuation", "Management & Capital", "Trends & Data", "AI Analyst", "📝 Full Report"])
    
    # TAB 1: VALUATION
    with tab1:
        st.subheader("Fair Value Calculator (DCF)")
        
        c1, c2 = st.columns([1, 1])
        divider = 1e6 
        
        with c1:
            st.markdown("#### 1. Your Assumptions")
            fcf_start = st.number_input("Starting FCF (M)", value=float(last['FCF']/divider)) * divider
            user_growth = st.slider("Growth 5y (%)", -5.0, 25.0, 5.0, key="g5_slider")
            wacc = st.slider("WACC (%)", 5.0, 15.0, 10.0, key="wacc_slider")
            gt = st.slider("Terminal Growth (%)", 0.0, 5.0, 2.0, key="gt_slider")

        with c2:
            st.markdown("#### 2. Results")
            fv = calculate_dcf(fcf_start, user_growth, gt, wacc, shares, nd)
            
            if fcf_start > 0 and price > 0:
                implied_growth = calculate_reverse_dcf(price, fcf_start, gt, wacc, shares, nd)
            else:
                implied_growth = 0

            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta", 
                value=fv,
                title={'text': f"Fair Value ({cur})"},
                delta={
                    'reference': price, 
                    'relative': True,
                    'valueformat': '.1%'
                },
                gauge={
                    'axis': {'range': [min(price, fv)*0.5, max(price, fv)*1.5]}, 
                    'bar': {'color': "#2E86C1"},
                    'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': price}
                }
            ))
            fig_gauge.update_layout(height=220, margin=dict(l=20,r=20,t=20,b=20))
            st.plotly_chart(fig_gauge, use_container_width=True)

            st.markdown("---")
            col_rev1, col_rev2 = st.columns(2)
            col_rev1.metric("Current Price", f"{price:.2f} {cur}")
            col_rev2.metric("Implied Growth", f"{implied_growth:.1f}%", delta=f"{user_growth - implied_growth:.1f}% vs Est.")

        with st.expander("See Piotroski Score Details"):
            st.write(f_details)
            
        # --- BLOC METRICS (Source: Yahoo Calculated) ---
        st.markdown("---")
        st.caption("📊 **Key Valuation Metrics (Calculated from Data)**")
        
        metrics_data = calculate_metrics_from_yahoo(df, info)

        if metrics_data:
            clean_data = {k: v for k, v in metrics_data.items() if v is not None and k != "Source"}
            metrics_df = pd.DataFrame(list(clean_data.items()), columns=["Metric", "Value"])
            
            def format_val(row):
                val = row['Value']
                if 'Yield' in row['Metric']: return f"{val * 100:.2f}%"
                if 'Graham' in row['Metric']: return f"{val:.2f} {cur}"
                return f"{val:.2f}x"

            metrics_df['Value'] = metrics_df.apply(format_val, axis=1)
            st.dataframe(metrics_df, use_container_width=True, hide_index=True)

    # TAB 2: MANAGEMENT (Governance)
    with tab2:
       st.subheader("Capital Allocation (Skin in the Game)")
       
       # Render Governance Component with real Yahoo Finance data
       render_governance_component(current_ticker)
       
       # --- PARTIE BUYBACK YIELD SUPPRIMÉE ---

    # TAB 3: TRENDS & DATA
    with tab3:
        # --- 1. Business Segments (Donut Chart) ---
        st.subheader("Business Segments")
        split_data = get_revenue_split_ai(current_ticker, st.session_state.active_name)
        
        if split_data:
            c_chart, c_txt = st.columns([2, 1])
            with c_chart:
                # --- CODE PERSONNALISÉ POUR LE DONUT SOMBRE ---
                labels = [item.get('label', 'Unknown') for item in split_data]
                values = [item.get('value', 0) for item in split_data]

                # Palette de couleurs "Sombres"
                dark_colors = ['#1A5276', '#922B21', '#117A65', '#6C3483', '#B9770E', '#283747']

                fig = go.Figure(data=[go.Pie(
                    labels=labels, 
                    values=values, 
                    hole=.4, 
                    marker=dict(colors=dark_colors, line=dict(color='white', width=1)),
                    textinfo='label+percent',
                    # 1. TAILLE RÉDUITE (12 au lieu de 14)
                    textfont=dict(size=12, color='white', family="Arial Black"),
                    textposition='inside',
                    # 2. FORCE LE TEXTE À RESTER DROIT (HORIZONTAL)
                    insidetextorientation='horizontal' 
                )])

                fig.update_layout(
                    title=dict(
                        text="Revenue Breakdown",
                        x=0.5,
                        xanchor='center',
                        yanchor='top',
                        font=dict(size=18, color='white')
                    ),
                    showlegend=False,
                    margin=dict(t=50, b=20, l=20, r=20),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                # ---------------------------------------------

            with c_txt:
                st.write("**Details:**")
                seg_df = pd.DataFrame(split_data)
                seg_df['value'] = seg_df['value'].astype(str) + '%'
                st.dataframe(seg_df, use_container_width=True, hide_index=True)
        else:
            st.info("Revenue segmentation unavailable.")
        
        # --- 2. Profitability Charts ---
        st.subheader("Profitability Trends")
        st.plotly_chart(render_profitability_chart(df), use_container_width=True, key="prof_chart")
        
        st.divider()

        # --- 3. Financial Data Tables ---
        fin_df = df.tail(5).copy()
        fin_df['Net_Income_Growth_YoY'] = fin_df['Net_Income'].pct_change() * 100
        
        cols_to_scale = ['Revenue', 'Net_Income', 'Operating_Cash_Flow', 'FCF', 'Cash_And_Equiv', 'Total_Debt', 'CapEx', 'Shares_Outstanding']
        for col in cols_to_scale:
            if col in fin_df.columns: fin_df[col] = fin_df[col] / 1e6

        fin_df.index = pd.to_datetime(fin_df.index).strftime('%Y-%m')
        
        cols_table1 = ['Revenue', 'Revenue_Growth_YoY', 'Net_Income', 'Net_Income_Growth_YoY', 'Operating_Cash_Flow']
        cols_table2 = ['FCF', 'Net_Margin', 'ROE', 'ROCE', 'Cash_And_Equiv', 'Total_Debt', 'CapEx', 'Shares_Outstanding']
        cols_table1 = [c for c in cols_table1 if c in fin_df.columns]
        cols_table2 = [c for c in cols_table2 if c in fin_df.columns]

        st.subheader(f"1. Growth & Earnings (in Millions of {cur})")
        df1 = fin_df[cols_table1].T
        df1 = df1[df1.columns[::-1]]
        st.dataframe(df1.style.format("{:.2f}"), use_container_width=True)

        st.subheader(f"2. Profitability & Health (in Millions of {cur})")
        df2 = fin_df[cols_table2].T
        df2 = df2[df2.columns[::-1]]
        st.dataframe(df2.style.format("{:.2f}"), use_container_width=True)

        # --- 4. SEC OFFICIAL DATA (RUST ENGINE) ---
        st.divider()
        st.markdown("### 🇺🇸 Official SEC Data (Powered by Rust Engine)")
        
        if "." not in current_ticker:
            sec_data = get_sec_data_rust(current_ticker)
            
            if sec_data:
                # --- MODIFICATION : ON A SUPPRIMÉ LE HEADER VISUEL ICI ---
                # (Plus de st.columns, plus de st.metric pour le CIK/Name)

                # --- PREPARATION DES DONNEES ---
                financials = sec_data.get('financials', {})
                
                if financials:
                    # 1. Organisation des données
                    data_map = {}
                    all_years = set()
                    
                    for metric, values in financials.items():
                        data_map[metric] = {y: v for y, v in values}
                        for y, _ in values: all_years.add(y)
                    
                    sorted_years = sorted(list(all_years), reverse=True)
                    plot_years = sorted(list(all_years))
                    
                    if not sorted_years:
                        st.warning("No complete year found.")
                        st.stop()

                    # --- 2. ALGORITHME DE CORRECTION DES SPLITS ---
                    if "Shares Outstanding" in data_map:
                        shares_map = data_map["Shares Outstanding"]
                        years = sorted([y for y in shares_map.keys()], reverse=True)
                        raw_shares = {y: shares_map[y] for y in years}
                        current_multiplier = 1.0
                        
                        for i in range(1, len(years)):
                            curr_y = years[i]
                            prev_y = years[i-1]
                            val_curr_raw = raw_shares.get(curr_y, 0)
                            val_prev_raw = raw_shares.get(prev_y, 0)
                            
                            if val_curr_raw < 1000 or val_prev_raw < 1000:
                                shares_map[curr_y] = val_curr_raw * current_multiplier
                                continue
                            
                            ratio = val_prev_raw / val_curr_raw
                            if ratio > 1.8: 
                                split_factor = round(ratio)
                                if 1 < split_factor <= 10: current_multiplier *= split_factor
                            elif ratio < 0.6: pass 
                            shares_map[curr_y] = val_curr_raw * current_multiplier

                    # --- 3. CALCULS KPI ---
                    data_map["Free Cash Flow"] = {}
                    data_map["ROE"] = {}
                    data_map["ROCE"] = {}
                    data_map["Net Margin"] = {}
                    data_map["EPS Diluted (Calc)"] = {} 
                    data_map["Adjusted FCF (ex-SBC)"] = {}
                    data_map["True FCF / Share"] = {}
                    
                    for y in sorted_years:
                        ni = data_map.get("Net Income", {}).get(y)
                        rev = data_map.get("Revenue", {}).get(y)
                        shares = data_map.get("Shares Outstanding", {}).get(y)
                        equity = data_map.get("Total Equity", {}).get(y)
                        ebit = data_map.get("Operating Income (EBIT)", {}).get(y)
                        ocf = data_map.get("Operating Cash Flow", {}).get(y)
                        capex = data_map.get("CapEx", {}).get(y)
                        sbc = data_map.get("SBC", {}).get(y, 0)
                        
                        # EPS
                        if ni is not None and shares is not None and shares > 0:
                            data_map["EPS Diluted (Calc)"][y] = ni / shares
                        else: data_map["EPS Diluted (Calc)"][y] = None

                        # FCF
                        fcf_val = None
                        if ocf is not None and capex is not None:
                            fcf_val = ocf - capex
                            data_map["Free Cash Flow"][y] = fcf_val
                        
                        # True FCF
                        if fcf_val is not None:
                            adj_fcf = fcf_val - sbc
                            data_map["Adjusted FCF (ex-SBC)"][y] = adj_fcf
                            if shares is not None and shares > 0:
                                data_map["True FCF / Share"][y] = adj_fcf / shares
                            
                        # Ratios
                        if ni is not None and equity is not None and equity != 0:
                            data_map["ROE"][y] = (ni / equity) * 100
                        if ni is not None and rev is not None and rev != 0:
                            data_map["Net Margin"][y] = (ni / rev) * 100
                        
                        debt = data_map.get("Long Term Debt", {}).get(y, 0)
                        cash = data_map.get("Cash & Equiv.", {}).get(y, 0)
                        if ebit is not None and equity is not None:
                            ce = equity + debt - cash
                            if ce != 0: data_map["ROCE"][y] = (ebit / ce) * 100

                    # --- 4. AFFICHAGE DES TABLEAUX ---
                    
                    # T1: MACRO
                    st.markdown("#### 💵 Key Financials (in Billions USD)")
                    metrics_macro = ["Revenue", "Operating Income (EBIT)", "Net Income", "Operating Cash Flow", "Free Cash Flow", "Total Equity", "Cash & Equiv.", "Long Term Debt"]
                    rows_macro = []
                    for metric in metrics_macro:
                        if metric in data_map and data_map[metric]:
                            row = [metric]
                            has_data = False
                            for y in sorted_years:
                                val = data_map[metric].get(y)
                                if val is not None:
                                    row.append(f"{val/1e9:.2f}")
                                    has_data = True
                                else: row.append("-")
                            if has_data: rows_macro.append(row)
                    if rows_macro: st.dataframe(pd.DataFrame(rows_macro, columns=["Metric"] + [str(y) for y in sorted_years]), use_container_width=True, hide_index=True)

                    # T2: RATIOS
                    st.markdown("#### 📉 Efficiency Ratios")
                    metrics_ratio = ["EPS Diluted (Calc)", "Shares Outstanding", "ROE", "ROCE", "Net Margin"]
                    rows_ratio = []
                    for metric in metrics_ratio:
                        if metric in data_map and data_map[metric]:
                            display_name = "EPS Diluted" if "EPS" in metric else metric
                            row = [display_name]
                            has_data = False
                            for y in sorted_years:
                                val = data_map[metric].get(y)
                                if val is not None:
                                    has_data = True
                                    if "EPS" in metric: row.append(f"{val:.2f} $")
                                    elif "Shares" in metric: row.append(f"{val/1e6:.0f} M")
                                    elif "ROE" in metric or "ROCE" in metric or "Margin" in metric: row.append(f"{val:.1f} %")
                                    else: row.append(f"{val:.2f}")
                                else: row.append("-")
                            if has_data: rows_ratio.append(row)
                    if rows_ratio: st.dataframe(pd.DataFrame(rows_ratio, columns=["Metric"] + [str(y) for y in sorted_years]), use_container_width=True, hide_index=True)

                    # T3: TRUE VALUE
                    st.markdown("#### 💎 True Owner Earnings (SBC Adjusted)")
                    metrics_true = ["Free Cash Flow", "SBC", "Adjusted FCF (ex-SBC)", "True FCF / Share"]
                    rows_true = []
                    for metric in metrics_true:
                        if metric in data_map and data_map[metric]:
                            row = [metric]
                            has_data = False
                            for y in sorted_years:
                                val = data_map[metric].get(y)
                                if val is not None:
                                    has_data = True
                                    if "Share" in metric: row.append(f"**{val:.2f} $**")
                                    else: row.append(f"{val/1e9:.2f}")
                                else: row.append("-")
                            if has_data: rows_true.append(row)
                    if rows_true: st.dataframe(pd.DataFrame(rows_true, columns=["Metric"] + [str(y) for y in sorted_years]), use_container_width=True, hide_index=True)

                    # --- T4: GROWTH CAGR (AUTO-ADAPTATIF) ---
                    
                    # 1. Trouver la dernière année "Complète" (qui a du Revenu)
                    latest_complete_year = None
                    for y in sorted_years:
                        if data_map["Revenue"].get(y) is not None:
                            latest_complete_year = y
                            break
                    if latest_complete_year is None: latest_complete_year = sorted_years[0]

                    st.markdown(f"#### 🚀 GROWTH per year (CAGR) - Ref: {latest_complete_year}")
                    
                    metrics_growth_config = [
                        ("Revenue", "Revenue"),
                        ("EPS Diluted (Calc)", "Diluted EPS"),
                        ("True FCF / Share", "True FCF/Share"),
                        ("Shares Outstanding", "Shares Outstanding Evolution")
                    ]
                    
                    rows_growth = []
                    periods = [1, 5, 10]
                    
                    for key, label in metrics_growth_config:
                        if key in data_map:
                            row = [label]
                            val_end = data_map[key].get(latest_complete_year)
                            
                            for p in periods:
                                start_year = latest_complete_year - p
                                val_start = data_map[key].get(start_year)
                                
                                if val_end is not None and val_start is not None and val_start != 0:
                                    try:
                                        if val_start < 0 and val_end > 0:
                                            row.append("Turnaround")
                                        elif val_start < 0 and val_end < 0:
                                            row.append("-")
                                        else:
                                            cagr = (abs(val_end) / abs(val_start)) ** (1/p) - 1
                                            if val_end < val_start: cagr = -abs(cagr)
                                            row.append(f"{cagr * 100:.1f}%")
                                    except:
                                        row.append("-")
                                else:
                                    row.append("-")
                            rows_growth.append(row)
                            
                    st.dataframe(pd.DataFrame(rows_growth, columns=["Metric", "1 Year", "5 Years", "10 Years"]), use_container_width=True, hide_index=True)

                    st.markdown("---")

                    # --- 5. GRAPHIQUES (HYBRIDES + FILTRE DATES + PRECISION DECIMALES) ---
                    st.markdown("#### 📊 Visual Trends")
                    
                    # CONFIGURATION : On a changé le format "{:.0f}" en "{:.2f}" pour Revenue et Net Income
                    charts_config = [
                        ("Revenue", "Revenue (Billions $)", 1e9, "#1f77b4", "{:.2f}"),      # <--- 2 décimales (ex: 1.28)
                        ("Net Income", "Net Income (Billions $)", 1e9, "#2ca02c", "{:.2f}"),  # <--- 2 décimales
                        ("EPS Diluted (Calc)", "EPS Diluted ($)", 1, "#00CC96", "{:.2f}"),
                        ("Shares Outstanding", "Shares Outstanding (Millions)", 1e6, "#EF553B", "{:.0f}"),
                        ("Adjusted FCF (ex-SBC)", "True FCF (ex-SBC) (Billions $)", 1e9, "#AB63FA", "{:.2f}"), # J'ai mis 2 décimales ici aussi pour la cohérence
                        ("True FCF / Share", "True FCF / Share ($)", 1, "#636efa", "{:.2f}"),
                        ("ROCE", "ROCE (%)", 1, "#e377c2", "{:.1f}%"),
                        ("Net Margin", "Net Margin (%)", 1, "#bcbd22", "{:.1f}%")
                    ]
                    
                    c_chart1, c_chart2 = st.columns(2)
                    
                    for i, (metric, title, scale, color, fmt) in enumerate(charts_config):
                        if metric in data_map:
                            # 1. FILTRAGE (On garde uniquement les années avec données)
                            filtered_years = []
                            filtered_vals = []
                            filtered_text = []
                            
                            for y in plot_years:
                                val = data_map[metric].get(y)
                                if val is not None:
                                    filtered_years.append(y)
                                    scaled_val = val / scale
                                    filtered_vals.append(scaled_val)
                                    filtered_text.append(fmt.format(scaled_val))
                            
                            if not filtered_years:
                                continue

                            # 2. CHOIX DU TYPE DE GRAPHIQUE
                            if metric in ["ROCE", "Net Margin"]:
                                # LIGNE pour les Ratios (%)
                                fig = go.Figure(go.Scatter(
                                    x=filtered_years, 
                                    y=filtered_vals, 
                                    mode='lines+markers+text',
                                    text=filtered_text, 
                                    textposition='top center', 
                                    name=metric, 
                                    line=dict(color=color, width=3),
                                    marker=dict(size=8, color=color)
                                ))
                            else:
                                # BARRES pour les Montants
                                fig = go.Figure(go.Bar(
                                    x=filtered_years, 
                                    y=filtered_vals, 
                                    text=filtered_text, 
                                    textposition='outside', 
                                    name=metric, 
                                    marker_color=color
                                ))
                            
                            # 3. MISE EN PAGE
                            # Configure y-axis: add padding for both bar charts and line charts to show text labels
                            yaxis_config = dict(showgrid=True, gridcolor='lightgray')
                            if filtered_vals:
                                max_val = max(filtered_vals)
                                min_val = min(filtered_vals)
                                if max_val > min_val:
                                    # Add padding: 15% above max for all charts to accommodate text labels
                                    if metric in ["ROCE", "Net Margin"]:
                                        # For line charts, maintain some bottom padding too
                                        range_padding = (max_val - min_val) * 0.15
                                        yaxis_config['range'] = [min_val - range_padding * 0.5, max_val + range_padding]
                                    else:
                                        # For bar charts, start from 0
                                        yaxis_config['range'] = [0, max_val * 1.15]
                            
                            fig.update_layout(
                                title=title, 
                                height=300, 
                                margin=dict(l=20, r=20, t=80, b=20), 
                                plot_bgcolor='rgba(0,0,0,0)', 
                                paper_bgcolor='rgba(0,0,0,0)', 
                                yaxis=yaxis_config,
                                xaxis=dict(type='category')
                            )
                            
                            if i % 2 == 0:
                                with c_chart1: st.plotly_chart(fig, use_container_width=True)
                            else:
                                with c_chart2: st.plotly_chart(fig, use_container_width=True)

                else:
                    st.info("Financial data not available in Rust JSON.")
            else:
                st.warning("Data not found.")
        else:
            st.info("US Stocks only.")
            
    # TAB 4: AI ANALYST & SENTIMENT
    with tab4:
        st.subheader("🤖 AI Sentiment & Earnings Analysis")
        
        # 1. Selecteur de mode avec KEY unique
        analysis_mode = st.radio(
            "Data Source:", 
            ["📰 Latest News (Auto)", "📝 Full Transcript (Manual)"], 
            horizontal=True,
            key="ai_mode_selector"  # <--- KEY IMPORTANTE
        )
        
        # --- MODE AUTOMATIQUE (GOOGLE NEWS) ---
        if analysis_mode == "📰 Latest News (Auto)":
            st.caption("Scanning Google News Finance for real sentiment analysis.")
            
            # Bouton avec KEY unique
            if st.button("🔍 Scan News & Analyze", key="btn_scan_news"): # <--- KEY AJOUTÉE
                with st.spinner(f"Fetching and analyzing for {current_ticker}..."):
                    try:
                        # 1. Récupération Google News RSS
                        url = f"https://news.google.com/rss/search?q={current_ticker}+stock+finance&hl=en-US&gl=US&ceid=US:en"
                        
                        response = requests.get(url, timeout=5)
                        soup = BeautifulSoup(response.content, features="xml")
                        
                        items = soup.findAll('item')
                        
                        full_text = ""
                        count = 0
                        # On prend les 12 premiers articles
                        for item in items[:12]:
                            title = item.title.text
                            pub_date = item.pubDate.text
                            full_text += f"- {title} ({pub_date})\n"
                            count += 1
                        
                        if count > 0:
                            # 2. Appel IA
                            from src.ai_engine import analyze_earnings_sentiment
                            ai_response = analyze_earnings_sentiment(current_ticker, full_text)
                            
                            # 3. STOCKAGE DANS LA SESSION
                            st.session_state.ai_analysis_result = ai_response
                            st.success(f"{count} articles successfully analyzed.")
                            
                        else:
                            st.error("No news found for this ticker.")
                            
                    except Exception as e:
                        st.error(f"Technical error: {e}")

        # --- MODE MANUEL ---
        else:
            st.caption("Copy-paste an Earnings Call transcript here.")
            raw_transcript = st.text_area("Paste text here", height=300, key="txt_manual_input") # Key ajoutée aussi ici
            
            # Bouton avec KEY unique
            if st.button("🧠 Analyze Transcript", key="btn_analyze_transcript"): # <--- KEY AJOUTÉE
                if len(raw_transcript) > 100:
                    with st.spinner("Psychological analysis in progress..."):
                        from src.ai_engine import analyze_earnings_sentiment
                        ai_response = analyze_earnings_sentiment(current_ticker, raw_transcript)
                        
                        # Stockage Session
                        st.session_state.ai_analysis_result = ai_response
                else:
                    st.warning("Text too short.")

        # --- AFFICHAGE DU RÉSULTAT (PERSISTANT) ---
        st.markdown("---")
        if st.session_state.ai_analysis_result:
            with st.chat_message("assistant"):
                st.markdown(st.session_state.ai_analysis_result)
                
            # Bouton avec KEY unique
            if st.button("Clear analysis", key="btn_clear_analysis"): # <--- KEY AJOUTÉE
                st.session_state.ai_analysis_result = None
                st.rerun()
            
# TAB 5: FULL REPORT GENERATOR
    with tab5:
        st.subheader("📝 Full Investment Report Generator")
        st.caption("This module uses the 'prompt.txt' file to generate a detailed investment thesis.")

        # 1. Lecture du fichier prompt.txt
        prompt_content = ""
        try:
            with open("prompt.txt", "r", encoding="utf-8") as f:
                prompt_content = f.read()
            st.success("✅ 'prompt.txt' file loaded successfully.")
            
            with st.expander("View used prompt template"):
                st.text(prompt_content)
                
        except FileNotFoundError:
            st.error("❌ 'prompt.txt' file not found at root.")
            st.stop()

        # 2. Préparation des données financières (String)
        # On transforme les 5 dernières années du dataframe en texte pour l'IA
        data_str_display = ""
        if not df.empty:
            # On sélectionne les colonnes clés
            cols_to_export = ['Revenue', 'Net_Income', 'EBIT', 'FCF', 'ROCE', 'Shares_Outstanding', 'Total_Debt']
            # On filtre celles qui existent vraiment
            existing_cols = [c for c in cols_to_export if c in df.columns]
            
            # On prend les 5 dernières lignes et on formate
            export_df = df[existing_cols].tail(5).copy()
            # Conversion en milliards pour lisibilité
            for c in ['Revenue', 'Net_Income', 'EBIT', 'FCF', 'Total_Debt']:
                if c in export_df.columns: export_df[c] = export_df[c] / 1e9
            
            data_str_display = export_df.to_string()
        else:
            data_str_display = "No financial data available."

        # 3. Bouton de Génération
        if st.button("🚀 Generate Report (Gemini Flash)", key="btn_full_report"):
            with st.spinner("Drafting investment thesis (this may take 30 seconds)..."):
                try:
                    # A. Injection des variables
                    final_prompt = prompt_content.format(
                        name=st.session_state.active_name,
                        ticker=current_ticker,
                        data_str=data_str_display
                    )
                    
                    # B. Appel IA
                    from src.ai_engine import generate_custom_analysis
                    result = generate_custom_analysis(final_prompt)
                    
                    # C. Stockage Session
                    st.session_state.full_report_result = result
                    
                    # --- D. SAUVEGARDE AUTOMATIQUE EN BDD (NOUVEAU) ---
                    if result and result.get("success"):
                        from src.database import save_ai_report
                        
                        saved = save_ai_report(
                            ticker=current_ticker,
                            name=st.session_state.active_name,
                            prompt=final_prompt,
                            model=result.get('model_used', 'Unknown'),
                            content=result.get('content', '')
                        )
                        
                        if saved:
                            st.toast("✅ Report archived in database!", icon="💾")
                        else:
                            st.error("⚠️ Error archiving to database.")
                    # ----------------------------------------------------

                except Exception as e:
                    st.error(f"Error during generation: {e}")

        # 4. Affichage du Rapport
        st.markdown("---")
        report_data = st.session_state.full_report_result

        if report_data:
            # Vérification si c'est une réussite ou une erreur
            if isinstance(report_data, dict) and report_data.get("success") is True:
                
                # --- A. METADONNEES TECHNIQUES (Le bandeau que vous vouliez) ---
                with st.expander("📊 AI Metrics & Costs", expanded=True):
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("AI Model", report_data['model_used'])
                    m2.metric("API Key Used", f"Key #{report_data['key_index']}")
                    m3.metric("Input Tokens", report_data['tokens_input'])
                    m4.metric("Output Tokens", report_data['tokens_output'])
                    st.caption(f"Total Tokens: **{report_data['tokens_total']}** (Context window used)")

                # --- B. LE RAPPORT ---
                st.markdown(report_data['content'])
                
                # --- C. TELECHARGEMENT ---
                st.download_button(
                    label="💾 Download Report (.md)",
                    data=report_data['content'],
                    file_name=f"Rapport_Investissement_{current_ticker}.md",
                    mime="text/markdown"
                )
            
            # Cas d'erreur renvoyé par le dictionnaire
            elif isinstance(report_data, dict) and report_data.get("success") is False:
                 st.error(report_data.get("error"))
            
            # Cas d'erreur générique (string)
            else:
                st.error(report_data) # Si c'est juste une string d'erreur
            
            # Bouton Effacer
            if st.button("Clear Report", key="btn_clear_report"):
                st.session_state.full_report_result = None
                st.rerun()