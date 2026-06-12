import numpy as np
import pandas as pd

def create_player_game_data(games_data, selected_player):
    player_game_data = games_data[(games_data['white_player'] == selected_player) | 
                                (games_data['black_player'] == selected_player)].copy()
    
    player_game_data['player_color'] = np.where(player_game_data['white_player'] == selected_player, 'White', 'Black')

    # 4. Dynamically assign their rating and opponent's rating
    player_game_data['player_rating'] = np.where(player_game_data['player_color'] == 'White', player_game_data['white_rating'], player_game_data['black_rating'])
    player_game_data['opponent_rating'] = np.where(player_game_data['player_color'] == 'White', player_game_data['black_rating'], player_game_data['white_rating'])

    # 5. Dynamically assign the Opponent's name
    player_game_data['opponent'] = np.where(player_game_data['player_color'] == 'White', player_game_data['black_player'], player_game_data['white_player'])

    # 6. Calculate the dynamic Outcome (Win / Loss / Draw)
    conditions = [
        (player_game_data['result'] == 'draw'),
        ((player_game_data['player_color'] == 'White') & (player_game_data['result'] == 'white')),
        ((player_game_data['player_color'] == 'Black') & (player_game_data['result'] == 'black'))
    ]
    choices = ['Draw', 'Win', 'Win']

    player_game_data['outcome'] = np.select(conditions, choices, default='Loss')

    return player_game_data