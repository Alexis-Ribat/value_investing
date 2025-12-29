import plotly.graph_objects as go
import pandas as pd
import streamlit as st
import yfinance as yf

def render_profitability_chart(df):
    """Renders the 5-year profitability trend chart."""
    chart_df = df.tail(5).copy()
    target_cols = ['ROE', 'ROCE', 'Net_Margin', 'Revenue_Growth_YoY']
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
                line=dict(color=color, width=3), 
                marker=dict(size=8, color=color, line=dict(width=2, color='white')),
                fill='tozeroy' if fill else 'none'
            ))

    add_trace('ROE', 'ROE', '#FF4B4B')
    add_trace('ROCE', 'ROCE', '#00CC96')
    add_trace('Net Margin', 'Net_Margin', '#636EFA') 
    add_trace('Growth', 'Revenue_Growth_YoY', '#FFA15A')

    fig.update_layout(
        height=450, 
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.2),
        margin=dict(t=20, b=60, l=20, r=20)
    )
    return fig
    
def render_capital_allocation_chart(df):
    """
    Affiche l'évolution du nombre d'actions (Dilution vs Buybacks) et le Dividende.
    """
    # Inverser pour avoir l'ordre chronologique (le plus vieux à gauche)
    chart_df = df.tail(5).iloc[::-1].copy()
    
    dates = pd.to_datetime(chart_df.index).strftime('%Y')
    
    fig = go.Figure()

    # 1. Barres pour le nombre d'actions (Shares Outstanding)
    # Si la barre baisse -> Buyback (Vert). Si elle monte -> Dilution (Rouge).
    
    # On calcule la variation pour la couleur, mais on affiche le total
    shares = chart_df['Shares_Outstanding']
    colors = ['#FFA15A'] * len(shares) # Couleur neutre par défaut
    
    # Logique couleur : on compare N vs N-1
    for i in range(1, len(shares)):
        if shares.iloc[i] < shares.iloc[i-1]:
            colors[i] = '#00CC96' # Vert (Buyback)
        elif shares.iloc[i] > shares.iloc[i-1]:
            colors[i] = '#FF4B4B' # Rouge (Dilution)

    fig.add_trace(go.Bar(
        x=dates,
        y=shares,
        name='Actions en circulation',
        marker_color=colors,
        opacity=0.6,
        yaxis='y1'
    ))

    # 2. Ligne pour le Dividende payé (si dispo dans les flux de tréso)
    # Yahoo met les dividendes payés en négatif dans le Cash Flow, on prend la valeur absolue
    # Note: Parfois c'est 'Dividends Paid', on essaie de le trouver
    div_cols = [c for c in df.columns if 'Dividend' in c]
    if div_cols:
        # Si on a une colonne dividende (dépend de yfinance data provider)
        # Pour l'instant on va utiliser une approximation via le Payout si on l'avait, 
        # mais restons simple : affichons le Net Income pour comparer.
        pass
    
    # Ajoutons plutôt le Net Income pour voir si le nombre d'actions baisse alors que le profit monte (Le Graal)
    fig.add_trace(go.Scatter(
        x=dates,
        y=chart_df['Net_Income'],
        name='Résultat Net',
        line=dict(color='white', width=3),
        yaxis='y2'
    ))

    fig.update_layout(
        title="Politique de Rachat d'Actions (Vert = Rachat / Rouge = Dilution)",
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", y=-0.2),
        margin=dict(t=40, b=40, l=20, r=20),
        yaxis=dict(title="Nombre d'actions", showgrid=False),
        yaxis2=dict(title="Résultat Net", overlaying='y', side='right', showgrid=False)
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
        
        # Get major holders breakdown
        insiders_pct = info.get('heldPercentInsiders', 0) or 0
        institutions_pct = info.get('heldPercentInstitutions', 0) or 0
        public_float_pct = 100 - insiders_pct - institutions_pct
        
        # Get top institutional holders
        institutional_holders = []
        try:
            if hasattr(stock, 'institutional_holders') and stock.institutional_holders is not None:
                df_inst = stock.institutional_holders
                for idx, row in df_inst.head(5).iterrows():
                    holder_name = row['Holder']
                    shares = row['Shares'] if 'Shares' in df_inst.columns else 0
                    pct_held = row['% Out'] if '% Out' in df_inst.columns else 0
                    
                    institutional_holders.append({
                        'holder': holder_name,
                        'shares': int(shares) if shares else 0,
                        'pct_held': float(pct_held) if pct_held else 0
                    })
        except:
            pass
        
        # Get insider roster
        insider_roster = []
        try:
            if hasattr(stock, 'insider_roster') and stock.insider_roster is not None:
                df_insiders = stock.insider_roster
                for idx, row in df_insiders.iterrows():
                    insider_roster.append({
                        'name': row.get('Name', 'Unknown'),
                        'position': row.get('Position', 'Unknown'),
                        'shares_held': int(row.get('Shares', 0)) if row.get('Shares') else 0
                    })
        except:
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
    Render governance dashboard with 3 zones:
    Zone 1: Ownership breakdown (Insiders %, Institutions %, Public Float %)
    Zone 2: Top 5 institutional holders (horizontal bars)
    Zone 3: Insider roster table sorted by shares held
    """
    gov_data = get_governance_data(ticker)
    
    if gov_data is None:
        st.warning("Unable to fetch governance data for this stock.")
        return
    
    # Zone 1: Ownership Breakdown Metrics
    st.subheader("Ownership Breakdown")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Insiders", f"{gov_data['insiders_pct']:.2f}%", 
                help="Percentage owned by company insiders")
    col2.metric("Institutions", f"{gov_data['institutions_pct']:.2f}%",
                help="Percentage owned by institutional investors")
    col3.metric("Public Float", f"{gov_data['public_float_pct']:.2f}%",
                help="Percentage available to public investors")
    
    st.divider()
    
    # Zone 2: Top 5 Institutional Holders
    if gov_data['institutional_holders']:
        st.subheader("Top 5 Institutional Holders")
        
        # Create horizontal bar chart
        df_inst = pd.DataFrame(gov_data['institutional_holders'])
        
        fig = go.Figure(data=[
            go.Bar(
                y=df_inst['holder'].head(5),
                x=df_inst['pct_held'].head(5),
                orientation='h',
                marker=dict(color='#2e5da3'),
                text=df_inst['pct_held'].head(5).apply(lambda x: f'{x:.2f}%'),
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title='',
            xaxis_title='% Held',
            yaxis_title='Holder',
            height=280,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            margin=dict(l=250, r=20, t=20, b=20),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No institutional holders data available for this stock.")
    
    st.divider()
    
    # Zone 3: Insider Roster Table
    if gov_data['insider_roster']:
        st.subheader("Management & Insiders")
        
        # Sort by shares held (descending)
        df_insiders = pd.DataFrame(gov_data['insider_roster'])
        df_insiders_sorted = df_insiders.sort_values('shares_held', ascending=False)
        
        # Format for display
        df_display = df_insiders_sorted[['name', 'position', 'shares_held']].copy()
        df_display.columns = ['Name', 'Position', 'Shares Held']
        df_display['Shares Held'] = df_display['Shares Held'].apply(lambda x: f"{int(x):,}")
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No insider roster data available for this stock.")
