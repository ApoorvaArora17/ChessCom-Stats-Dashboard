from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests
import time
from tqdm import tqdm

HEADERS = {
    "User-Agent": "ChessGameAnalyzer/1.0 (arora.apoorva02@gmail.com)"
}


def get_all_games(username):
    # Step 1: Get archive URLs
    archives_url = f"https://api.chess.com/pub/player/{username}/games/archives"
    response = requests.get(archives_url, headers=HEADERS)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch archives: {response.status_code}")

    archives = response.json().get("archives", [])
    print(f"Found {len(archives)} monthly archives.")

    all_games = []

    # Step 2: Download each archive with a progress bar
    # We wrap the 'archives' list in tqdm() to track the loop
    for archive_url in tqdm(archives, desc="Downloading monthly archives", unit="month"):
        archive_response = requests.get(archive_url, headers=HEADERS)

        if archive_response.status_code != 200:
            # tqdm.write ensures your print statements don't break the progress bar layout
            tqdm.write(f"Skipping broken archive: {archive_url}")
            continue

        games = archive_response.json().get("games", [])
        all_games.extend(games)

        # Be polite to Chess.com
        time.sleep(0.1)

    print(f"\nTotal games fetched: {len(all_games)}")
    return all_games


def get_games_month(username, year, month):
    url = f"https://api.chess.com/pub/player/{username}/games/{year}/{month}"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        print("Failed to fetch games.")
        return None
        
    games = response.json().get("games", [])
    if not games:
        print("No games found for this period.")
        return None
        
    return games


def get_games_range(username, start_yrMth, end_yrMth):
    """
    Fetches all chess games for a user within a specific month range.
    Expected format for start_yrMth and end_yrMth: "YYYY-MM" (e.g., "2023-01")
    """
    # 1. Parse the input strings into datetime objects
    try:
        start_date = datetime.strptime(start_yrMth, "%Y-%m")
        end_date = datetime.strptime(end_yrMth, "%Y-%m")
    except ValueError:
        print("Invalid date format. Please use 'YYYY-MM'.")
        return None

    if start_date > end_date:
        print("Start date must be before or equal to end date.")
        return None

    all_games = []
    current_date = start_date

    # 2. Loop through each month until we pass the end_date
    while current_date <= end_date:
        # Format year and month to match the API expectations (e.g., '2023', '01')
        year_str = current_date.strftime("%Y")
        month_str = current_date.strftime("%m")
        
        print(f"Fetching games for {year_str}-{month_str}...")
        month_games = get_games_month(username, year_str, month_str)
        
        if month_games:
            all_games.extend(month_games)
            
        # Move to the next month using dateutil's relativedelta
        current_date += relativedelta(months=1)

    if not all_games:
        print("No games found for the entire period.")
        return None

    print(f"Successfully fetched a total of {len(all_games)} games.")
    return all_games
    