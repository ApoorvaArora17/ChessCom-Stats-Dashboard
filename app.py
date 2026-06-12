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
# 2. DATA LOADING & SIMULATED TRANSFORMATION FUNCTION
# -------------------------------------------------------------
@st.cache_data
def load_base_data():
    """Loads the base raw CSV game data."""
    try:
        # Replace with your actual filename, e.g., 'games_data.csv'
        df = pd.read_csv('all_games.csv')            
        return df
    except FileNotFoundError:
        # TEMPORARY: Return a mock dataframe if file doesn't exist yet so code runs safely
        return create_mock_data()

def load_available_players():
    """ Loads a list of all available players """
    try:
        df = pd.read_csv('available_players.csv')
        return df
    except FileNotFoundError:
        return pd.DataFrame({'username':'apoorva_arora'})
# -------------------------------------------------------------
# 3. SIDEBAR CONTROLS
# -------------------------------------------------------------
st.sidebar.title("♟️ Dashboard Navigation")
st.sidebar.markdown("---")

df_raw = load_base_data()
available_players = load_available_players()

# 1. Get game counts for players as White and as Black
all_players = available_players['username'].tolist()

# User Selection Input
selected_user = st.sidebar.selectbox("🎯 Select Friend to Analyze:", all_players)

st.sidebar.markdown("### Filters")
show_all_games = st.sidebar.checkbox("Include Variants & Daily Games", value=False)

# Apply default rules if checkbox is empty
if not show_all_games:
    # Keep only standard chess and filter out slow daily games
    df_processed = df_raw[(df_raw['game_type'] == 'chess') & (df_raw['time_class'] != 'daily')].copy()
else:
    df_processed = df_raw.copy()

# Run your core perspective transformation matrix
player_df = create_player_game_data(df_processed, selected_user)


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
    
    current_rating = int(player_df.sort_values(by='start_datetime', ascending=False)['player_rating'].iloc[0])
    peak_rating = int(player_df['player_rating'].max())

    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Total Games Played", total_games)
    m_col2.metric("Win Rate", f"{win_rate:.1f}%")
    m_col3.metric("Current Elo Rating", current_rating)
    m_col4.metric("Lifetime Peak Elo", peak_rating)
    
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
        fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_pie, use_container_width=True)

    with chart_col2:
        st.subheader("📈 Elo Progression Over Time")
        # Ensure sorting is chronological for the line chart
        line_df = player_df.sort_values(by='start_datetime')
        fig_line = px.line(
            line_df, x='start_datetime', y='player_rating',
            labels={'player_rating': 'Elo Rating', 'start_datetime': 'Date'},
            render_mode='svg'
        )
        fig_line.update_traces(line_color='#3498db', line_width=2.5)
        st.plotly_chart(fig_line, use_container_width=True)

    st.markdown("---")

    # ---- LAYER 3: STRATEGIC INSIGHTS ----
    st.subheader("🧠 Deep Playstyle Breakdown")
    strat_col1, strat_col2 = st.columns(2)

    with strat_col1:
        st.markdown("#### ⚔️ Most Deadly Openings")
        # Calculate opening win rates with a minimum threshold of 3 games
        opening_stats = player_df.groupby('opening_name').agg(
            Played=('outcome', 'count'),
            Win_Rate=('outcome', lambda x: (x == 'Win').sum() / len(x) * 100)
        ).reset_index()
        
        top_openings = opening_stats[opening_stats['Played'] >= 3].sort_values(by='Win_Rate', ascending=False).head(5)
        
        if not top_openings.empty:
            fig_openings = px.bar(
                top_openings, x='Win_Rate', y='opening_name', 
                orientation='h', text_auto='.1f',
                labels={'Win_Rate': 'Win Rate (%)', 'opening_name': 'Opening'},
                color='Win_Rate', color_continuous_scale='Greens'
            )
            fig_openings.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
            st.plotly_chart(fig_openings, use_container_width=True)
        else:
            st.info("Play at least 3 games with an opening family to unlock opening analysis.")

    with strat_col2:
        st.markdown("#### ⏱️ Game Termination Fingerprints")
        # Shows how your friend wins or loses games
        fig_term = px.histogram(
            player_df, y='result_type', color='outcome',
            orientation='h', barmode='stack',
            labels={'win_type': 'How Game Ended', 'count': 'Number of Games'},
            color_discrete_map={'Win': '#2ecc71', 'Loss': '#e74c3c', 'Draw': '#7f8c8d'}
        )
        fig_term.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_term, use_container_width=True)


# -------------------------------------------------------------
# APPENDIX: HELPER FUNCTION TO GENERATE CLEAN MOCK DATA
# -------------------------------------------------------------
def create_mock_data():
    """Generates clean structural sample data if games_data.csv isn't provided."""
    import random
    np.random.seed(42)
    rows = 120
    openings = ['Sicilian Defense', 'Ruy Lopez', 'French Defense', 'Caro-Kann Defense', 'Queens Gambit']
    types = ['checkmated', 'resigned', 'timeout', 'repetition']
    
    data = {
        'game_type': ['chess'] * rows,
        'time_class': ['blitz' if i % 2 == 0 else 'rapid' for i in range(rows)],
        'white_player': [random.choice(['manteghanand', 'kzwo', 'GrandmasterPro']) for _ in range(rows)],
        'black_player': [random.choice(['manteghanand', 'kzwo', 'GrandmasterPro']) for _ in range(rows)],
        'winner': [random.choice(['white', 'black', 'draw']) for _ in range(rows)],
        'win_type': [random.choice(types) for _ in range(rows)],
        'white_rating': [random.randint(1300, 1500) for _ in range(rows)],
        'black_rating': [random.randint(1300, 1500) for _ in range(rows)],
        'opening_name': [random.choice(openings) for _ in range(rows)],
        'start_datetime': pd.date_range(start='2026-01-01', periods=rows, freq='D')
    }
    # Ensure they don't play against themselves in mock generation
    df = pd.DataFrame(data)
    df = df[df['white_player'] != df['black_player']].copy()
    return df