import requests
import pandas as pd
import time

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

def merge_players(sam_df, gavin_df):
    # Merge the two dataframes on the appid
    sam_games_df = sam_df
    gavin_games_df = gavin_df
    if not sam_games_df.empty and not gavin_games_df.empty:
        # Make sure appid is a column in both dataframes
        merged_df = pd.merge(sam_games_df, gavin_games_df, on="appid", how="outer", suffixes=('_Sam', '_Gavin'))
        
        # For game names, use one version
        if 'name_Sam' in merged_df.columns and 'name_Gavin' in merged_df.columns:
            merged_df['Game'] = merged_df['name_Sam'].combine_first(merged_df['name_Gavin'])
            merged_df.drop(['name_Sam', 'name_Gavin'], axis=1, inplace=True)
        
        # Set the index to game name
        merged_df.set_index("Game", inplace=True)
        
        # Sort by Gavin's playtime
        if 'playtime_forever_Sam' in merged_df.columns:
            merged_df.sort_values(by="playtime_forever_Gavin", ascending=False, inplace=True)
        
        # Fill NaN values with 0 for playtime columns
        for col in merged_df.columns:
            if 'playtime' in col or 'rtime' in col:
                merged_df[col] = merged_df[col].fillna(0)
        
        df = merged_df
        return df
    else:
        if not sam_games_df.empty:
            df = sam_games_df
        elif not gavin_games_df.empty:
            df = gavin_games_df
        else:
            df = pd.DataFrame()
            print("Could not retrieve games data for either user.")
        return df

def get_store_data(appid):
    store_url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=us&l=en"
    try:
        data = make_request(store_url)
        # Check if data is None before trying to access it
        if data is None:
            print(f"No data returned for appid {appid}")
            return None
        
        if str(appid) in data and data[str(appid)]["success"]:
            return data[str(appid)]["data"]
        else:
            print(f"No success data for appid {appid}")
            return None
    except Exception as e:
        print(f"Error getting store data for appid {appid}: {e}")
        return None

def get_review_data(appid):
    review_url = f"https://store.steampowered.com/appreviews/{appid}?json=1&language=all"
    try:
        data = make_request(review_url)
        if data and "query_summary" in data:
            summary = data['query_summary']
            desc = summary.get("review_score_desc")
            positive = summary.get("total_positive")
            negative = summary.get("total_negative")
            return desc, positive, negative
        else:
            return None, None, None
    except Exception as e:
        print(f"Error getting review data for appid {appid}: {e}")
        return None, None, None
    
def merge_game_data(df):
    # Initialize lists to store data
    genres = []
    prices = []
    review_descriptions = []
    positive_ratios = []
    negative_ratios = []


    # Loop through each game in our dataframe
    for appid in df["appid"]:
        try:
            game_data = get_store_data(appid)
            review_desc, positive_ratio, negative_ratio = get_review_data(appid)
            time.sleep(0.2)  # We will be a little bit kind to steam and rate limit ourselves 😺

            if game_data:
                # Get genre(s)
                genre_list = game_data.get("genres")
                genre_names = [g["description"] for g in genre_list]
                genres.append(", ".join(genre_names) if genre_names else None)

                # Get price
                try:
                    price_info = game_data["price_overview"]    
                    prices.append(price_info["final"] / 100)  # Prices in dollars
                except KeyError:
                    prices.append(0.0)
            else:
                genres.append(None)
                prices.append(None)
            
            review_descriptions.append(review_desc)
            positive_ratios.append(positive_ratio)
            negative_ratios.append(negative_ratio)
        except Exception as e:
            print(f"Error processing appid {appid}: {e}")
            # Add empty values to keep lists aligned
            genres.append(None)
            prices.append(None)
            review_descriptions.append(None)
            positive_ratios.append(None)
            negative_ratios.append(None)

    # Now update dataframe with our new data
    df["Genre"] = genres
    df["Price (USD $)"] = prices
    df["Review Score"] = review_descriptions
    df["Total Positive Reviews"] = positive_ratios
    df["Total Negative Reviews"] = negative_ratios

    # save to a csv file (optional)
    # df.to_csv("steam_games_data.csv")

