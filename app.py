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

@st.cache_data
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
selected_user = st.sidebar.selectbox("🎯 Select Player to Analyze:", all_players)

st.sidebar.markdown("### Global Filters")
show_all_games = st.sidebar.checkbox("Include Variants & Daily Games", value=False)

# Pre-filter the raw data based on variants rule
if not show_all_games:
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

# Set up default fallback state for control selector variable
selected_control = 'All Controls'

if not player_df.empty:
    available_controls = ['All Controls'] + sorted(player_df['time_control'].dropna().unique().tolist())
    selected_control = st.sidebar.selectbox("Select Time Control:", available_controls)

    if selected_control != 'All Controls':
        player_df = player_df[player_df['time_control'] == selected_control]


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
    
    # --- TIME & MOVE CALCULATIONS ---
    time_col = 'game_duration_seconds'
    
    # Standard field mapping safety check for move logs
    moves_col = 'num_moves'
    
    if time_col in player_df.columns:
        total_seconds = player_df[time_col].sum()
        avg_seconds = player_df[time_col].mean() if total_games > 0 else 0
        total_hours = total_seconds / 3600
        
        avg_minutes = int(avg_seconds // 60)
        avg_remaining_seconds = int(avg_seconds % 60)
        avg_time_str = f"{avg_minutes}m {avg_remaining_seconds}s" if total_games > 0 else "0m 0s"
    else:
        total_hours = 0.0
        avg_time_str = "N/A"

    # Evaluate structural criteria gates for Elo milestones
    is_singular_format = 'selected_format' in locals() and selected_format != 'All Formats'
    is_control_filtered = selected_control != 'All Controls'

    # Only show Current/Peak Elo metrics if a single format is active AND no specific time control is selected
    if is_singular_format and not is_control_filtered:
        current_rating = int(player_df.sort_values(by='start_datetime', ascending=False)['player_rating'].iloc[0])
        peak_rating = int(player_df['player_rating'].max())

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Games Played", total_games)
        col2.metric("Win Rate", f"{win_rate:.1f}%")
        col3.metric("Total Time Invested", f"{total_hours:.1f} Hours")
        
        col4, col5, col6 = st.columns(3)
        col4.metric(f"Current {selected_format.title()} Elo", current_rating)
        col5.metric(f"Peak {selected_format.title()} Elo", peak_rating)
        col6.metric("Avg. Game Duration", avg_time_str)
    else:
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Total Games Played", total_games)
        m_col2.metric("Win Rate", f"{win_rate:.1f}%")
        m_col3.metric("Total Time Invested", f"{total_hours:.1f} Hours")
        m_col4.metric("Avg. Game Duration", avg_time_str)
        
        if is_control_filtered:
            st.info("💡 Elo progression graphs and peak rating thresholds are hidden while filtering by sub-time controls.")
        
    st.markdown("---")

    # ---- LAYER 2: CORE VISUALIZATIONS ----
    if is_control_filtered:
        st.subheader("📋 Match Outcome Breakdown")
        fig_pie = px.pie(
            player_df, names='outcome', 
            color='outcome',
            color_discrete_map={'Win': '#2ecc71', 'Loss': '#e74c3c', 'Draw': '#7f8c8d'},
            hole=0.4
        )
        fig_pie.update_traces(
            textinfo='value+percent', 
            texttemplate='%{value} games<br>(%{percent})'
        )
        fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.subheader("📋 Match Outcome Breakdown")
            fig_pie = px.pie(
                player_df, names='outcome', 
                color='outcome',
                color_discrete_map={'Win': '#2ecc71', 'Loss': '#e74c3c', 'Draw': '#7f8c8d'},
                hole=0.4
            )
            fig_pie.update_traces(
                textinfo='value+percent', 
                texttemplate='%{value} games<br>(%{percent})'
            )
            fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_pie, use_container_width=True)

        with chart_col2:
            st.subheader("📈 Elo Progression Over Time")
            line_df = player_df.sort_values(by='start_datetime')
            
            if line_df.empty:
                st.info("No rating data available for this selection.")
            else:
                if selected_format == 'All Formats':
                    fig_line = px.line(
                        line_df, x='start_datetime', y='player_rating',
                        color='time_class',
                        labels={'player_rating': 'Elo Rating', 'start_datetime': 'Date', 'time_class': 'Format'},
                        render_mode='svg'
                    )
                    fig_line.update_traces(line_shape='hv')
                else:
                    fig_line = px.line(
                        line_df, x='start_datetime', y='player_rating',
                        labels={'player_rating': 'Elo Rating', 'start_datetime': 'Date'},
                        render_mode='svg'
                    )
                    fig_line.update_traces(line_color='#3498db', line_width=2.5, line_shape='hv')
                    
                fig_line.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig_line, use_container_width=True)

    st.markdown("---")

    # ---- LAYER 3: PLAYSTYLE DURATION & PACE ANALYSIS ----
    st.subheader("🧠 Playstyle Velocity & Engagement Insights")
    
    analysis_col1, analysis_col2 = st.columns(2)
    
    # COLUMN 1: DURATION ANALYSIS
    with analysis_col1:
        st.markdown("#### ⏱️ Average Game Duration by Outcome")
        if time_col in player_df.columns and not player_df.empty:
            duration_df = player_df.groupby(['time_class', 'outcome'])[time_col].mean().reset_index()
            duration_df['avg_minutes'] = duration_df[time_col] / 60
            
            fig_time_bar = px.bar(
                duration_df, 
                x='time_class', 
                y='avg_minutes',
                color='outcome',
                barmode='group',
                labels={'avg_minutes': 'Minutes', 'outcome': 'Outcome', 'time_class': 'Format'},
                color_discrete_map={'Win': '#2ecc71', 'Loss': '#e74c3c', 'Draw': '#7f8c8d'},
                text_auto='.1f'
            )
            fig_time_bar.update_traces(textposition='outside')
            fig_time_bar.update_layout(
                yaxis_title="Duration (Minutes)",
                xaxis_title="Game Format",
                margin=dict(t=10, b=10, l=10, r=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_time_bar, use_container_width=True)
        else:
            st.info("🕒 Game duration data columns missing from active logs.")

    # COLUMN 2: MOVE COUNT ANALYSIS
    with analysis_col2:
        st.markdown("#### 🔄 Average Move Count by Outcome")
        if moves_col and not player_df.empty:
            # Aggregate based on your log's dynamically located move count field
            moves_df = player_df.groupby(['time_class', 'outcome'])[moves_col].mean().reset_index()
            
            fig_moves_bar = px.bar(
                moves_df, 
                x='time_class', 
                y=moves_col,
                color='outcome',
                barmode='group',
                labels={moves_col: 'Moves', 'outcome': 'Outcome', 'time_class': 'Format'},
                color_discrete_map={'Win': '#2ecc71', 'Loss': '#e74c3c', 'Draw': '#7f8c8d'},
                text_auto='.0f' # Whole integers make sense for tracking move counts cleanly
            )
            fig_moves_bar.update_traces(textposition='outside')
            fig_moves_bar.update_layout(
                yaxis_title="Average Total Moves",
                xaxis_title="Game Format",
                margin=dict(t=10, b=10, l=10, r=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_moves_bar, use_container_width=True)
        else:
            st.info("♟️ Move count identification field (e.g., 'move_count' or 'moves') missing from active logs.")