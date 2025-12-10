from src.hoopland.data.nba_client import NBAClient
import pandas as pd

try:
    client = NBAClient()
    # Using '2003' to check LeBron/Darko
    df = client.get_draft_history(season_year='2003')
    print("Columns:", df.columns.tolist())
    
    if not df.empty:
        # Print LeBron (Pick 1) and Darko (Pick 2)
        print("\nLeBron Data:")
        print(df[df['OVERALL_PICK'] == 1].iloc[0])
        print("\nDarko Data:")
        print(df[df['OVERALL_PICK'] == 2].iloc[0])
except Exception as e:
    print(e)
