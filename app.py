import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from final_data_creation_funcs import create_player_game_data

# -------------------------------------------------------------
# 1. PAGE SETUP & CONFIGURATION
# -------------------------------------------------------------
st.set_page_config(
    page_title="Chess.com Stats",
    page_icon="♟️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling for metrics cards to look slick
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #2ecc71;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)


# -------------------------------------------------------------
# 2. DATA LOADING
# -------------------------------------------------------------
@st.cache_data
def load_base_data():
    """Loads the base raw CSV game data."""
    return pd.read_csv('all_games.csv')            

def load_available_players():
    """ Loads a list of all available players """
    return pd.read_csv('available_players.csv')


# -------------------------------------------------------------
# 3. SIDEBAR CONTROLS & GLOBAL FILTERS
# -------------------------------------------------------------
st.sidebar.title("♟️ Dashboard Navigation")
st.sidebar.markdown("---")

df_raw = load_base_data()
available_players = load_available_players()

# Extract available players list
all_players = available_players['username'].tolist()

# User Selection Input
selected_user = st.sidebar.selectbox("🎯 Select Friend to Analyze:", all_players)

st.sidebar.markdown("### Global Filters")
show_all_games = st.sidebar.checkbox("Include Variants & Daily Games", value=False)

# Pre-filter the raw data based on variants rule
if not show_all_games:
    # Keep only standard chess and filter out slow daily games
    df_variants_filtered = df_raw[(df_raw['game_type'] == 'chess') & (df_raw['time_class'] != 'daily')].copy()
else:
    df_variants_filtered = df_raw.copy()

# Run your core perspective transformation matrix to get player-specific data
player_df_full = create_player_game_data(df_variants_filtered, selected_user)

# Global Time Class Filter
if not player_df_full.empty:
    available_formats = ['All Formats'] + sorted(player_df_full['time_class'].dropna().unique().tolist())
    selected_format = st.sidebar.selectbox("⏱️ Select Game Format:", available_formats)
    
    # Apply the global filter to the final player dataframe
    if selected_format != 'All Formats':
        player_df = player_df_full[player_df_full['time_class'] == selected_format]
    else:
        player_df = player_df_full.copy()
else:
    player_df = player_df_full.copy()


# -------------------------------------------------------------
# 4. MAIN DASHBOARD RENDER
# -------------------------------------------------------------
if player_df.empty:
    st.warning(f"No games found matching the active filters for **{selected_user}**.")
else:
    st.title(f"📊 Performance Insights: {selected_user}")
    st.markdown(f"Analyzing **{len(player_df)}** games filtered down from the master logs.")
    st.markdown("---")

    # ---- LAYER 1: HEADLINE METRICS ----
    total_games = len(player_df)
    wins = len(player_df[player_df['outcome'] == 'Win'])
    losses = len(player_df[player_df['outcome'] == 'Loss'])
    draws = len(player_df[player_df['outcome'] == 'Draw'])
    win_rate = (wins / total_games) * 100 if total_games > 0 else 0
    
    # Check if a singular time class format is active
    is_singular_format = 'selected_format' in locals() and selected_format != 'All Formats'

    if is_singular_format:
        # Calculate Elo metrics cleanly for a single format pool
        current_rating = int(player_df.sort_values(by='start_datetime', ascending=False)['player_rating'].iloc[0])
        peak_rating = int(player_df['player_rating'].max())

        # Render 4 columns with Elo data included
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Total Games Played", total_games)
        m_col2.metric("Win Rate", f"{win_rate:.1f}%")
        m_col3.metric(f"Current {selected_format.title()} Elo", current_rating)
        m_col4.metric(f"Peak {selected_format.title()} Elo", peak_rating)
    else:
        # Render only 2 clean columns for overall summary when multiple formats are mixed
        m_col1, m_col2 = st.columns(2)
        m_col1.metric("Total Games Played (All Formats)", total_games)
        m_col2.metric("Overall Combined Win Rate", f"{win_rate:.1f}%")
    
    st.markdown("---")

    # ---- LAYER 2: CORE VISUALIZATIONS ----
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("📋 Match Outcome Breakdown")
        fig_pie = px.pie(
            player_df, names='outcome', 
            color='outcome',
            color_discrete_map={'Win': '#2ecc71', 'Loss': '#e74c3c', 'Draw': '#7f8c8d'},
            hole=0.4
        )
        
        # --- UPDATED: Force chart to show both the raw count (value) and the percentage ---
        fig_pie.update_traces(
            textinfo='value+percent', 
            texttemplate='%{value} games<br>(%{percent})' # Clean layout formatting with a line break
        )
        
        fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_pie, use_container_width=True)

    with chart_col2:
        st.subheader("📈 Elo Progression Over Time")
        
        # Ensure sorting is chronological for the line chart
        line_df = player_df.sort_values(by='start_datetime')
        
        if line_df.empty:
            st.info("No rating data available for this selection.")
        else:
            # If tracking 'All Formats', split lines visually by time_class
            if selected_format == 'All Formats':
                fig_line = px.line(
                    line_df, x='start_datetime', y='player_rating',
                    color='time_class',
                    labels={'player_rating': 'Elo Rating', 'start_datetime': 'Date', 'time_class': 'Format'},
                    render_mode='svg'
                )
                # --- UPDATED: Apply stepped line to all format streams ---
                fig_line.update_traces(line_shape='hv')
            else:
                # If a specific format is selected globally, show one single clean focused line
                fig_line = px.line(
                    line_df, x='start_datetime', y='player_rating',
                    labels={'player_rating': 'Elo Rating', 'start_datetime': 'Date'},
                    render_mode='svg'
                )
                # --- UPDATED: Apply stepped line and color/width settings ---
                fig_line.update_traces(line_color='#3498db', line_width=2.5, line_shape='hv')
                
            fig_line.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_line, use_container_width=True)