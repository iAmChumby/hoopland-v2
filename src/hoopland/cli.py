import argparse
import logging
import sys
import os
from src.hoopland.blocks.generator import Generator
from src.hoopland.logger import setup_logger

# Ensure logs directory exists (handled by logger now, but keeping for safety if needed before logger init)
# os.makedirs("logs", exist_ok=True) 

# Initial basic setup for stdout before args are parsed
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Hoopland V2 Generator CLI")
    parser.add_argument(
        "--league",
        type=str,
        choices=["nba", "ncaa", "draft"],
        default="nba",
        help="Type of generation",
    )
    parser.add_argument(
        "--year", type=str, required=True, help="Year to generate (e.g. 2003)"
    )
    parser.add_argument(
        "--tournament",
        action="store_true",
        help="NCAA only: Limit to 64 tournament teams instead of full 362",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Setup file logging based on arguments
    setup_logger(mode=args.league, year=args.year)

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")

    logger.info(f"Starting generation for {args.league.upper()} {args.year}")

    try:
        generator = Generator()

        if args.league == "nba":
            league = generator.generate_league(args.year)
            filename = f"NBA_{args.year}_League.txt"
        elif args.league == "draft":
            league = generator.generate_draft_class(args.year)
            filename = f"NBA_{args.year}_Draft_Class.txt"
        elif args.league == "ncaa":
            tournament_mode = args.tournament
            league = generator.generate_ncaa_league(args.year, tournament_mode=tournament_mode)
            suffix = "_Tournament" if tournament_mode else ""
            filename = f"NCAA_{args.year}{suffix}_League.txt"

        # Save Output
        generator.to_json(league, filename)
        logger.info(f"Successfully generated {filename}")

    except Exception as e:
        logger.exception(f"Generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
