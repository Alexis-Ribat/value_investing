import plotly.graph_objects as go
import pandas as pd
import streamlit as st
import yfinance as yf

def render_profitability_chart(df):
    """Renders the profitability trend chart (Removed Growth)."""
    chart_df = df.tail(5).copy()
    # J'ai retiré 'Revenue_Growth_YoY' de la liste ci-dessous
    target_cols = ['ROE', 'ROCE', 'Net_Margin'] 
    valid_cols = [c for c in target_cols if c in chart_df.columns]
    
    # Filter cleanup
    chart_df[valid_cols] = chart_df[valid_cols].fillna(0)
    chart_df = chart_df[(chart_df[valid_cols] != 0).any(axis=1)]

    fig = go.Figure()
    raw_dates = chart_df['Date'] if 'Date' in chart_df.columns else chart_df.index
    chart_dates = pd.to_datetime(raw_dates).dt.strftime('%Y')

    def add_trace(name, col, color, fill=False):
        if col in chart_df.columns:
            fig.add_trace(go.Scatter(
                x=chart_dates, 
                y=chart_df[col], 
                name=name, 
                mode='lines+markers', 
                line=dict(color=color, width=3), # Largeur conservée
                marker=dict(size=8, color=color, line=dict(width=2, color='white')),
                fill='tozeroy' if fill else 'none'
            ))

    add_trace('ROE', 'ROE', '#FF4B4B')
    add_trace('ROCE', 'ROCE', '#00CC96')
    add_trace('Net Margin', 'Net_Margin', '#636EFA') 
    # La ligne Growth a été supprimée ici

    fig.update_layout(
        height=450, 
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.2), # Légende en bas conservée
        margin=dict(t=20, b=60, l=20, r=20)
    )
    return fig

    
def render_revenue_donut(data):
    """
    Renders a Donut chart from AI-generated JSON data.
    Data format: [{'label': 'Name', 'value': 10}, ...]
    """
    if not data: return go.Figure()
    
    labels = [item['label'] for item in data]
    values = [item['value'] for item in data]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=.4, # Makes it a donut
        marker=dict(colors=['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A'])
    )])

    fig.update_layout(
        title="Revenue Breakdown (Estimated)",
        height=350,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="v", y=0.5),
        margin=dict(t=40, b=20, l=20, r=20)
    )
    
    return fig


@st.cache_data(ttl=86400)
def get_governance_data(ticker):
    """
    Fetch governance data from Yahoo Finance.
    Returns insiders %, institutions %, top institutional holders, and insider roster.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Récupération du nombre total d'actions pour le calcul manuel
        total_shares = info.get('sharesOutstanding', 0)

        # 1. Répartition globale
        insiders_pct = (info.get('heldPercentInsiders', 0) or 0) * 100
        institutions_pct = (info.get('heldPercentInstitutions', 0) or 0) * 100
        
        public_float_pct = 100 - insiders_pct - institutions_pct
        if public_float_pct < 0: public_float_pct = 0
        
        # 2. Top Institutional Holders
        institutional_holders = []
        try:
            if hasattr(stock, 'institutional_holders') and stock.institutional_holders is not None:
                df_inst = stock.institutional_holders
                if not df_inst.empty:
                    for idx, row in df_inst.head(5).iterrows():
                        holder_name = row.get('Holder', 'Unknown')
                        shares = row.get('Shares', 0)
                        
                        # --- CORRECTION ICI : CALCUL MANUEL DU % ---
                        # Au lieu de lire la colonne '% Out' qui est souvent buggée (0),
                        # on calcule : (Actions détenues / Total Actions) * 100
                        if total_shares > 0 and shares > 0:
                            calculated_pct = (shares / total_shares) * 100
                        else:
                            # Fallback si on ne peut pas calculer, on essaie de lire la colonne existante
                            raw_pct = row.get('% Out', 0)
                            calculated_pct = float(raw_pct) * 100 if float(raw_pct) < 1 else float(raw_pct)

                        institutional_holders.append({
                            'holder': holder_name,
                            'shares': int(shares),
                            'pct_held': calculated_pct 
                        })
        except Exception as e:
            pass
        
        # 3. Insider Roster
        insider_roster = []
        try:
            target_df = None
            if hasattr(stock, 'insiders') and stock.insiders is not None:
                target_df = stock.insiders
            elif hasattr(stock, 'insider_roster') and stock.insider_roster is not None:
                target_df = stock.insider_roster
            
            if target_df is not None and not target_df.empty:
                for idx, row in target_df.iterrows():
                    position = str(row.get('Position', 'Unknown'))
                    if len(position) > 30: position = position[:27] + "..."

                    insider_roster.append({
                        'name': row.get('Name', 'Unknown'),
                        'position': position,
                        'shares_held': int(row.get('Shares', 0)) if row.get('Shares') else 0
                    })
        except Exception:
            pass
        
        return {
            'insiders_pct': insiders_pct,
            'institutions_pct': institutions_pct,
            'public_float_pct': public_float_pct,
            'institutional_holders': institutional_holders,
            'insider_roster': insider_roster
        }
    except Exception as e:
        print(f"Error fetching governance data: {e}")
        return None

def render_governance_component(ticker):
    """
    Render governance dashboard with 3 zones.
    Updated: Donut chart text orientation set to horizontal.
    """
    gov_data = get_governance_data(ticker)
    
    if gov_data is None:
        st.warning("Unable to fetch governance data for this stock.")
        return
    
    # --- ZONE 1 : Ownership Breakdown (Metrics) ---
    st.subheader("Ownership Breakdown")
    
    # Affichage des métriques sur une ligne
    col1, col2, col3 = st.columns(3)
    col1.metric("Insiders", f"{gov_data['insiders_pct']:.2f}%", 
                help="Percentage owned by company insiders")
    col2.metric("Institutions", f"{gov_data['institutions_pct']:.2f}%",
                help="Percentage owned by institutional investors")
    col3.metric("Public Float", f"{gov_data['public_float_pct']:.2f}%",
                help="Percentage available to public investors")
    
    st.caption("Répartition du capital entre les initiés (management), les grands fonds et le public.")

    # --- ZONE 1 (Suite) : Le Camembert (Chart) ---
    
    labels = ['Insiders', 'Institutions', 'Public Float']
    values = [
        gov_data['insiders_pct'], 
        gov_data['institutions_pct'], 
        gov_data['public_float_pct']
    ]
    
    # Couleurs sombres
    colors = ['#006400', '#191970', '#363636'] 

    fig_donut = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=.4, 
        marker=dict(colors=colors, line=dict(color='#1E1E1E', width=2)),
        textinfo='label+percent',
        # --- TEXTE EN GRAS ET BLANC ---
        textfont=dict(size=14, color='white', family="Arial Black"),
        texttemplate="<b>%{label}</b><br><b>%{percent}</b>",
        hoverinfo='label+percent+value',
        # --- NOUVEAU : FORCE LE TEXTE HORIZONTAL ---
        insidetextorientation='horizontal'
    )])

    fig_donut.update_layout(
        title=dict(
            text="Ownership Distribution",
            x=0.5,
            y=0.95,
            xanchor='center',
            yanchor='top',
            font=dict(size=20, color='white')
        ),
        height=350,
        showlegend=False,
        margin=dict(t=60, b=20, l=20, r=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    
    st.plotly_chart(fig_donut, use_container_width=True)

    st.divider()
    
    # --- ZONE 2 : Top 5 Institutional Holders (Tableau) ---
    if gov_data['institutional_holders']:
        st.subheader("Top 5 Institutional Holders")
        
        df_inst = pd.DataFrame(gov_data['institutional_holders'])
        df_display_inst = df_inst[['holder', 'pct_held']].copy()
        df_display_inst.columns = ['Institutional Holder', '% Held']
        df_display_inst['% Held'] = df_display_inst['% Held'].apply(lambda x: f"{x:.2f}%")
        
        st.table(df_display_inst)
    else:
        st.info("No institutional holders data available for this stock.")
    
    st.divider()
    
