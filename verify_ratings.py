import json
import os

game_file = r"output/2016/NCAA_2016_Tournament_League.txt"


def verify():
    if not os.path.exists(game_file):
        print("File not found.")
        return

    with open(game_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    stars_to_check = [
        "Jaylen Brown",
        "Jamal Murray",
        "Jalen Brunson",
        "Ben Simmons",
        "Buddy Hield",
    ]

    tier_counts = {"Future Star": 0, "Star": 0, "Starter": 0, "Role": 0, "Bench": 0}
    total = 0

    print(f"\nScanning {len(data['teams'])} teams...")

    for team in data["teams"]:
        for p in team.get("roster", []):
            name = f"{p.get('fn', '')} {p.get('ln', '')}".strip()

            attrs = p["attributes"]
            avg_base = sum(val[0] for val in attrs.values()) / len(attrs)
            avg_pot = sum(val[1] for val in attrs.values()) / len(attrs)

            # Simple heuristic
            if avg_base >= 7:
                tier = "Future Star/Star"
            elif avg_base >= 6:
                tier = "Star"
            elif avg_base >= 4:
                tier = "Starter"
            elif avg_base >= 3:
                tier = "Role"
            else:
                tier = "Bench"

            # Specific check for stars
            if name in stars_to_check:
                print(
                    f"[*] {name}: Rating={p['rating']}, Pot={p['pot']} | Attributes Base Avg={avg_base:.2f}, Pot Avg={avg_pot:.2f}"
                )

            # Distribution check
            # Rating is now stars (0.5-5.0), so 5.0 is max (score 10)
            # 4.5 is high star (score 9)
            if p["rating"] >= 4.5:
                tier_counts["Future Star"] += 1
            elif p["rating"] >= 4.0:
                tier_counts["Star"] += 1
            elif p["rating"] >= 3.0:
                tier_counts["Starter"] += 1
            elif p["rating"] >= 2.0:
                tier_counts["Role"] += 1
            else:
                tier_counts["Bench"] += 1
            total += 1

    print("\n--- Distribution ---")
    for k, v in tier_counts.items():
        print(f"{k}: {v} ({v/total*100:.1f}%)")


verify()
