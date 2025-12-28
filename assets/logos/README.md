# Logo Assets

This directory contains logo images for leagues and teams used by the Hoopland generator.

## Directory Structure

```
assets/logos/
├── leagues/
│   ├── nba.png       # NBA league logo
│   └── ncaa.png      # NCAA league logo
└── teams/
    └── nba/
        ├── atl-hawks.png
        ├── bos-celtics.png
        ├── bkn-nets.png
        ├── sea-supersonics.png   # Historical team
        ├── nj-nets.png           # Historical team
        ├── van-grizzlies.png     # Historical team
        └── ... (all current + historical teams)
```

## Logo URL Format

Once logos are added, update the `historical_teams.json` file with the logo URLs.

For GitHub-hosted logos, use raw URLs like:
```
https://raw.githubusercontent.com/<username>/<repo>/main/assets/logos/teams/nba/atl-hawks.png
```

## Historical Teams Requiring Logos

These teams have relocated and need separate historical logos:

| Team ID | Historical Name | Years | Logo File |
|---------|----------------|-------|-----------|
| 1610612760 | Seattle SuperSonics | 1967-2008 | sea-supersonics.png |
| 1610612751 | New Jersey Nets | 1977-2012 | nj-nets.png |
| 1610612751 | New York Nets | 1968-1977 | ny-nets.png |
| 1610612763 | Vancouver Grizzlies | 1995-2001 | van-grizzlies.png |
| 1610612740 | Charlotte Hornets | 1988-2002 | chh-hornets.png |
| 1610612744 | San Francisco Warriors | 1962-1971 | sf-warriors.png |
| 1610612744 | Philadelphia Warriors | 1946-1962 | phi-warriors.png |
| 1610612745 | San Diego Rockets | 1967-1971 | sd-rockets.png |
| 1610612762 | New Orleans Jazz | 1974-1979 | no-jazz.png |
| 1610612764 | Washington Bullets | 1974-1997 | was-bullets.png |
| 1610612764 | Baltimore Bullets | 1963-1973 | bal-bullets.png |
| 1610612746 | San Diego Clippers | 1978-1984 | sd-clippers.png |
| 1610612746 | Buffalo Braves | 1970-1978 | buf-braves.png |

## Recommended Image Specifications

- Format: PNG with transparency
- Size: 512x512 pixels (will be scaled in-game)
- Background: Transparent
