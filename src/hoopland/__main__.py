import sys
import argparse
from .workflows import refresh_nba_data, export_player_json


def main():
    parser = argparse.ArgumentParser(description="Hoop Land CLI")
    parser.add_argument("action", choices=["sync", "export"], help="Action to perform")
    parser.add_argument("--player", help="Player name for export")

    args = parser.parse_args()

    if args.action == "sync":
        refresh_nba_data()
    elif args.action == "export":
        if not args.player:
            print("Please provide --player name")
            sys.exit(1)
        export_player_json(args.player)


if __name__ == "__main__":
    main()
