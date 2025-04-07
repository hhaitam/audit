import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(layout="wide", page_title="Micromania Analytics")

# Load and prepare data
@st.cache_data
def load_data():
    df = pd.read_csv('micromania_donnees_fictives.csv', sep=';')
    
    # Calculate additional metrics
    df['CA par employé'] = df['Chiffre d\'Affaires Annuel (€)'] / df['Nombre d\'Employés']
    df['CA par m²'] = df['Chiffre d\'Affaires Annuel (€)'] / df['Surface (m²)']
    df['Taille'] = pd.cut(df['Surface (m²)'], 
                         bins=[0, 200, 350, 500],
                         labels=['Petit (<200m²)', 'Moyen (200-350m²)', 'Grand (>350m²)'])
    
    # Convert opening date to datetime and extract year
    df['Date d\'Ouverture'] = pd.to_datetime(df['Date d\'Ouverture'])
    df['Année d\'Ouverture'] = df['Date d\'Ouverture'].dt.year
    
    return df

df = load_data()

# Dashboard layout
st.title("📊 Tableau de Bord Micromania")

# Sidebar filters
st.sidebar.header("Filtres")
selected_cities = st.sidebar.multiselect("Villes", options=df['Ville'].unique(), default=df['Ville'].unique())
selected_sizes = st.sidebar.multiselect("Taille de magasin", options=df['Taille'].unique(), default=df['Taille'].unique())
min_employees = st.sidebar.slider("Employés minimum", min_value=1, max_value=20, value=1)
year_range = st.sidebar.slider("Année d'ouverture", 
                              min_value=2015, 
                              max_value=2025, 
                              value=(2015, 2025))

# Apply filters
filtered_df = df[
    (df['Ville'].isin(selected_cities)) &
    (df['Taille'].isin(selected_sizes)) &
    (df['Nombre d\'Employés'] >= min_employees) &
    (df['Année d\'Ouverture'].between(year_range[0], year_range[1]))
]

# KPI Cards
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Nombre de magasins", len(filtered_df))
with col2:
    st.metric("CA total (M€)", f"{filtered_df['Chiffre d\'Affaires Annuel (€)'].sum()/1e6:.2f}")
with col3:
    st.metric("CA moyen par magasin (k€)", f"{filtered_df['Chiffre d\'Affaires Annuel (€)'].mean()/1e3:.1f}")
with col4:
    st.metric("Employés total", filtered_df['Nombre d\'Employés'].sum())

# Main tabs
tab1, tab2, tab3 = st.tabs(["Analyse Globale", "Comparaisons", "Répartition"])

with tab1:
    # Radar Chart - Maturity Analysis
    st.subheader("Radar de Maturité des Magasins")
    
    # Calculate maturity scores (example metrics)
    radar_df = filtered_df.groupby('Taille').agg({
        'CA par employé': 'mean',
        'CA par m²': 'mean',
        'Nombre de Transactions': 'mean',
        'Nombre d\'Employés': 'mean',
        'Surface (m²)': 'mean'
    }).reset_index()
    
    # Normalize scores for radar chart
    radar_df_normalized = radar_df.copy()
    for col in ['CA par employé', 'CA par m²', 'Nombre de Transactions', 'Nombre d\'Employés', 'Surface (m²)']:
        radar_df_normalized[col] = (radar_df[col] - radar_df[col].min()) / (radar_df[col].max() - radar_df[col].min()) * 100
    
    fig_radar = go.Figure()
    
    for _, row in radar_df_normalized.iterrows():
        fig_radar.add_trace(go.Scatterpolar(
            r=[row['CA par employé'], row['CA par m²'], row['Nombre de Transactions'], 
              row['Nombre d\'Employés'], row['Surface (m²)']],
            theta=['CA/Employé', 'CA/m²', 'Transactions', 'Employés', 'Surface'],
            name=row['Taille'],
            fill='toself'
        ))
    
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        height=500
    )
    st.plotly_chart(fig_radar, use_container_width=True)

with tab2:
    # Bar Chart - Comparative Analysis
    st.subheader("Comparaison des Performances")
    
    comparison_metric = st.selectbox(
        "Métrique à comparer",
        options=['Chiffre d\'Affaires Annuel (€)', 'Nombre de Transactions', 'CA par employé', 'CA par m²'],
        index=0
    )
    
    group_by = st.selectbox(
        "Grouper par",
        options=['Ville', 'Taille', 'Année d\'Ouverture'],
        index=1
    )
    
    bar_df = filtered_df.groupby(group_by)[comparison_metric].mean().reset_index()
    
    fig_bar = px.bar(
        bar_df,
        x=group_by,
        y=comparison_metric,
        color=group_by,
        text_auto='.2s',
        title=f"{comparison_metric} par {group_by}"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with tab3:
    # Pie Chart - Distribution Analysis
    st.subheader("Répartition des Données")
    
    distribution_metric = st.selectbox(
        "Métrique de répartition",
        options=['Chiffre d\'Affaires Annuel (€)', 'Nombre de Transactions', 'Nombre d\'Employés'],
        index=0
    )
    
    group_by_pie = st.selectbox(
        "Segmenter par",
        options=['Taille', 'Ville', 'Année d\'Ouverture'],
        index=0
    )
    
    pie_df = filtered_df.groupby(group_by_pie)[distribution_metric].sum().reset_index()
    
    fig_pie = px.pie(
        pie_df,
        names=group_by_pie,
        values=distribution_metric,
        hole=0.3,
        title=f"Répartition du {distribution_metric} par {group_by_pie}"
    )
    st.plotly_chart(fig_pie, use_container_width=True)