import requests
import pandas as pd

def make_request(url):
    """
    Takes in an input url and returns the data as a json object
    """
    response = requests.get(url)
    data = response.json()

    return data

def get_user_games(api_key, steam_id, name):
    url = f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={api_key}&steamid={steam_id}&include_appinfo=1&format=json"
    data = make_request(url)

    # Process data
    if 'response' in data and 'games' in data['response']:
        games_list = data["response"]["games"]

        # Convert list of games to a dataframe
        df = pd.DataFrame(games_list)

        # Add a column suffix to separate Sam's and Gavin's data
        playtime_cols=["playtime_forever", "playtime_windows_forever", "playtime_2weeks", "rtime_last_played"]
        for col in playtime_cols:
            if col in df.columns:
                df.rename(columns={col: f"{col}_{name}"}, inplace=True)
        return df
    
    else:
        print(f"Error getting games for {name}.")
        return pd.DataFrame()

def drop_columns(df, name):
    df.drop(columns=[f"playtime_windows_forever_{name}", f"playtime_mac_forever_{name}", f"playtime_linux_forever_{name}", f"playtime_deck_forever_{name}", f"content_descriptorids_{name}", f"playtime_disconnected_{name}", f"img_icon_url_{name}", f"has_leaderboards_{name}", f"has_community_visible_stats_{name}"], inplace=True)
    return df
