import plotly.graph_objects as go
import pandas as pd
import streamlit as st

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

# --- MOCK DATA FOR MAJOR SHAREHOLDERS ---
# Replace this with API call to fetch real shareholder data
MOCK_SHAREHOLDERS_DATA = {
    "shareholders": [
        {
            "name": "Christian Dior SE",
            "shares": 209504613,
            "percentage": 42.1,
            "valuation_eur": 155000000  # Mock value in EUR
        },
        {
            "name": "Arnault Family",
            "shares": 35669321,
            "percentage": 7.2,
            "valuation_eur": 26307000
        },
        {
            "name": "OFI Invest Asset Management SA",
            "shares": 697528,
            "percentage": 0.14,
            "valuation_eur": 514000
        },
        {
            "name": "Rothschild & Co Asset Management",
            "shares": 426829,
            "percentage": 0.086,
            "valuation_eur": 315000
        },
        {
            "name": "State Street Global Advisors",
            "shares": 369770,
            "percentage": 0.074,
            "valuation_eur": 273000
        },
        {
            "name": "Float/Unknown",
            "shares": 300000000,
            "percentage": 48.3,
            "valuation_eur": 220000000
        }
    ],
    "distribution_by_type": [
        {"label": "Christian Dior SE", "value": 42.1, "color": "#1f3a7d"},
        {"label": "Individuals/Family", "value": 7.2, "color": "#2e5da3"},
        {"label": "Institutional Investors", "value": 2.18, "color": "#4a90e2"},
        {"label": "Float/Unknown", "value": 48.3, "color": "#8fb3f5"}
    ]
}

def render_major_shareholders(shareholders_data=None):
    """
    Renders a Major Shareholders section with responsive layout.
    Left: Table of shareholders
    Right: Donut chart of ownership distribution
    
    Args:
        shareholders_data: Dict with 'shareholders' list and 'distribution_by_type' list.
                          If None, uses MOCK_SHAREHOLDERS_DATA
    """
    if shareholders_data is None:
        shareholders_data = MOCK_SHAREHOLDERS_DATA
    
    # Create two columns for responsive layout
    col_table, col_chart = st.columns([1.2, 1])
    
    # --- LEFT SIDE: SHAREHOLDERS TABLE ---
    with col_table:
        st.subheader("Principal Actionnaires")
        
        # Convert to DataFrame for clean display
        shareholders_list = shareholders_data.get("shareholders", [])
        if shareholders_list:
            df_shareholders = pd.DataFrame(shareholders_list)
            
            # Format the display dataframe
            df_display = df_shareholders.copy()
            df_display['Nombre d\'Actions'] = df_display['shares'].apply(lambda x: f"{x:,.0f}")
            df_display['% Détenu'] = df_display['percentage'].apply(lambda x: f"{x:.2f}%")
            df_display['Valuation (€)'] = df_display['valuation_eur'].apply(lambda x: f"€{x/1e6:.1f}M" if x >= 1e6 else f"€{x/1e3:.0f}K")
            
            # Select columns to display
            df_display = df_display[['name', 'Nombre d\'Actions', '% Détenu', 'Valuation (€)']]
            df_display.columns = ['Nom', 'Nombre d\'Actions', '% Détenu', 'Valuation (€)']
            
            # Display with Streamlit dataframe
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True
            )
    
    # --- RIGHT SIDE: OWNERSHIP DISTRIBUTION CHART ---
    with col_chart:
        st.subheader("Répartition")
        
        distribution_data = shareholders_data.get("distribution_by_type", [])
        if distribution_data:
            labels = [item['label'] for item in distribution_data]
            values = [item['value'] for item in distribution_data]
            colors = [item.get('color', '#636EFA') for item in distribution_data]
            
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.4,  # Donut chart
                marker=dict(colors=colors, line=dict(color='rgba(0,0,0,0)', width=2)),
                textposition='inside',
                textinfo='label+percent',
                hovertemplate='<b>%{label}</b><br>%{value:.1f}%<extra></extra>'
            )])
            
            fig.update_layout(
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white', size=12),
                margin=dict(t=40, b=20, l=20, r=20),
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.0,
                    bgcolor='rgba(0,0,0,0)',
                    bordercolor='rgba(255,255,255,0.2)',
                    borderwidth=1
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)