"""
Coordinate utilities for converting between real-world coordinates and game coordinates.

The game coordinate system appears to use:
- x = latitude * 100
- y = longitude * 100 * -1
"""

import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def lat_lng_to_game_coords(lat: float, lng: float) -> Dict[str, int]:
    """
    Convert latitude/longitude coordinates to game coordinate system.

    Args:
        lat: Latitude in decimal degrees
        lng: Longitude in decimal degrees

    Returns:
        Dict with 'x' and 'y' keys containing game coordinates
    """
    # Based on analysis of NBA coordinates:
    # x ≈ latitude * 100
    # y ≈ longitude * 100 (NBA stores western longitudes as negative)
    game_x = round(lat * 100)
    game_y = round(lng * 100)

    return {"x": game_x, "y": game_y}


def game_coords_to_lat_lng(x: int, y: int) -> Tuple[float, float]:
    """
    Convert game coordinates back to latitude/longitude.

    Args:
        x: Game x coordinate
        y: Game y coordinate

    Returns:
        Tuple of (latitude, longitude)
    """
    lat = x / 100.0
    lng = (y / 100.0) * -1
    return lat, lng


# Pre-defined coordinates for common NCAA schools
# This serves as a fallback/manual override for schools that are hard to geocode
SCHOOL_COORDINATES = {
    "Abilene Christian": (32.4697, -99.7081),
    "Air Force": (38.9972, -104.5464),
    "Akron": (41.0814, -81.5190),
    "Alabama": (33.2140, -87.5391),
    "Alabama A&M": (34.7839, -86.5722),
    "Alabama State": (32.3643, -86.2954),
    "Albany": (42.6850, -73.8250),
    "Alcorn State": (31.8744, -91.1408),
    "American University": (38.9379, -77.0903),
    "Appalachian State": (36.2137, -81.6912),
    "Arizona": (32.2319, -110.9501),
    "Arizona State": (33.4242, -111.9281),
    "Arkansas": (36.0678, -94.1734),
    "Arkansas Pine-Bluff": (34.2455, -92.0059),
    "Arkansas State": (35.8423, -90.6785),
    "Arkansas-Little Rock": (34.7237, -92.3586),
    "Army": (41.3929, -73.9613),
    "Auburn": (32.6099, -85.4808),
    "Austin Peay": (36.5316, -87.3553),
    "Ball State": (40.1998, -85.4106),
    "Baylor": (31.5489, -97.1131),
    "Bellarmine": (38.2203, -85.6969),
    "Belmont": (36.1327, -86.7958),
    "Bethune-Cookman": (29.2108, -81.0228),
    "Binghamton": (42.0894, -75.9697),
    "Boise State": (43.6036, -114.2939),
    "Boston College": (42.3355, -71.1685),
    "Boston University": (42.3505, -71.1054),
    "Bowling Green": (41.3759, -83.6513),
    "Bradley": (40.6965, -89.6166),
    "Brigham Young": (40.2518, -111.6493),
    "Brown": (41.8268, -71.4025),
    "Bryant": (41.9202, -71.5514),
    "Bucknell": (40.9548, -76.8844),
    "Buffalo": (42.8864, -78.8784),
    "Butler": (39.8403, -86.1607),
    "Cal Poly": (35.3009, -120.6625),
    "Cal State Bakersfield": (35.3505, -119.1023),
    "Cal State Fullerton": (33.8823, -117.8854),
    "Cal State Northridge": (34.2413, -118.5283),
    "California": (37.8715, -122.2730),
    "California Baptist": (33.9253, -117.3961),
    "Campbell": (35.4088, -78.7386),
    "Canisius": (42.9256, -78.8539),
    "Central Arkansas": (35.0887, -92.4413),
    "Central Connecticut": (41.6937, -72.7662),
    "Central Florida": (28.6024, -81.2001),
    "Central Michigan": (43.5820, -84.7730),
    "Central Oklahoma": (35.6572, -97.4708),
    "Charleston": (32.7833, -79.9361),
    "Charleston Southern": (32.7833, -79.9361),
    "Charlotte": (35.2271, -80.8431),
    "Chattanooga": (35.0456, -85.3097),
    "Chicago State": (41.7188, -87.6091),
    "Cincinnati": (39.1329, -84.5144),
    "Clemson": (34.6834, -82.8374),
    "Cleveland State": (41.5023, -81.6758),
    "Coastal Carolina": (33.7958, -78.7811),
    "Colgate": (42.8192, -75.5446),
    "Colorado": (40.0076, -105.2659),
    "Colorado State": (40.5734, -105.0865),
    "Columbia": (40.8075, -73.9626),
    "Connecticut": (41.8077, -72.2540),
    "Coppin State": (39.3126, -76.5305),
    "Cornell": (42.4534, -76.4735),
    "Creighton": (41.2654, -95.9478),
    "Dartmouth": (43.7044, -72.2887),
    "Davidson": (35.5011, -80.8485),
    "Dayton": (39.7589, -84.1916),
    "Delaware": (39.6781, -75.7507),
    "Delaware State": (39.1877, -75.5416),
    "Denver": (39.7392, -104.9903),
    "DePaul": (41.9245, -87.6565),
    "Detroit Mercy": (42.3314, -83.0458),
    "Drake": (41.6005, -93.6532),
    "Drexel": (39.9526, -75.1652),
    "Duke": (36.0014, -78.9382),
    "Duquesne": (40.4374, -79.9901),
    "East Carolina": (35.6065, -77.3664),
    "East Tennessee State": (36.3048, -82.3668),
    "Eastern Illinois": (39.4817, -88.1754),
    "Eastern Kentucky": (37.7450, -84.4494),
    "Eastern Michigan": (42.2458, -83.6263),
    "Eastern Washington": (47.4914, -117.5858),
    "Elon": (36.1029, -79.5023),
    "Evansville": (37.9748, -87.5558),
    "Fairfield": (41.1607, -73.2454),
    "Fairleigh Dickinson": (40.8968, -74.0337),
    "Florida": (29.6516, -82.3248),
    "Florida A&M": (30.4272, -84.2807),
    "Florida Atlantic": (26.3706, -80.1025),
    "Florida Gulf Coast": (26.4640, -81.7744),
    "Florida International": (25.7564, -80.3756),
    "Florida State": (30.4419, -84.2985),
    "Fordham": (40.8617, -73.8857),
    "Fresno State": (36.8123, -119.7462),
    "Furman": (34.9229, -82.4388),
    "Gardner-Webb": (35.2495, -81.6601),
    "George Mason": (38.8304, -77.3076),
    "George Washington": (38.8995, -77.0486),
    "Georgetown": (38.9076, -77.0723),
    "Georgia": (33.9480, -83.3773),
    "Georgia Southern": (32.4207, -81.7840),
    "Georgia State": (33.7531, -84.3853),
    "Georgia Tech": (33.7756, -84.3963),
    "Gonzaga": (47.6671, -117.4016),
    "Grambling": (32.5222, -92.7149),
    "Grand Canyon": (33.5101, -112.1286),
    "Green Bay": (44.5192, -88.0198),
    "Hampton": (37.0237, -76.3344),
    "Hartford": (41.7658, -72.7145),
    "Harvard": (42.3770, -71.1167),
    "Hawaii": (21.3069, -157.8583),
    "High Point": (35.9729, -79.9960),
    "Hofstra": (40.7167, -73.5996),
    "Holy Cross": (42.2379, -71.8079),
    "Houston": (29.7604, -95.3698),
    "Houston Christian": (29.8260, -95.3964),
    "Howard": (38.9224, -77.0194),
    "Idaho": (46.7296, -114.0071),
    "Idaho State": (42.8628, -112.4504),
    "Illinois": (40.1019, -88.2272),
    "Illinois Chicago": (41.8715, -87.6464),
    "Illinois State": (40.5083, -88.9937),
    "Incarnate Word": (29.4674, -98.4824),
    "Indiana": (39.1653, -86.5264),
    "Indiana State": (39.4650, -87.4139),
    "Iona": (40.9264, -73.7846),
    "Iowa": (41.6627, -91.5549),
    "Iowa State": (42.0266, -93.6465),
    "Jackson State": (32.2988, -90.1848),
    "Jacksonville": (30.3322, -81.6557),
    "Jacksonville State": (33.8223, -85.7694),
    "James Madison": (38.4351, -78.8698),
    "Kansas": (38.9543, -95.2558),
    "Kansas State": (39.1974, -96.5847),
    "Kennesaw State": (34.0380, -84.5816),
    "Kent State": (41.1456, -81.3392),
    "Kentucky": (38.0307, -84.5037),
    "La Salle": (40.0386, -75.1551),
    "Lafayette": (40.6976, -75.2091),
    "Lamar": (30.0424, -94.0750),
    "Lehigh": (40.6070, -75.3774),
    "Liberty": (37.3541, -79.1794),
    "Lipscomb": (36.1041, -86.7904),
    "Long Beach State": (33.7838, -118.1141),
    "Longwood": (36.6915, -78.8964),
    "Louisiana": (30.4133, -91.1800),
    "Louisiana Monroe": (32.5260, -92.0726),
    "Louisiana Tech": (32.5223, -92.6493),
    "Louisville": (38.2527, -85.7585),
    "Loyola Chicago": (41.9981, -87.6596),
    "Loyola Maryland": (39.3469, -76.6183),
    "Loyola Marymount": (33.9703, -118.4181),
    "LSU": (30.4120, -91.1833),
    "Maine": (44.8995, -68.6724),
    "Manhattan": (40.8101, -73.9608),
    "Marist": (41.7225, -73.9341),
    "Marquette": (43.0388, -87.9286),
    "Marshall": (38.4220, -82.4244),
    "Maryland": (38.9869, -76.9426),
    "Maryland Eastern Shore": (38.2116, -75.6866),
    "Massachusetts": (42.4084, -71.1185),
    "McNeese State": (30.1745, -93.2153),
    "Memphis": (35.1174, -89.9711),
    "Mercer": (32.8277, -83.6499),
    "Miami": (25.7617, -80.1918),
    "Miami (OH)": (39.5092, -84.7321),
    "Michigan": (42.2780, -83.7382),
    "Michigan State": (42.7018, -84.4822),
    "Middle Tennessee": (35.8492, -86.3656),
    "Milwaukee": (43.0389, -87.9065),
    "Minnesota": (44.9778, -93.2650),
    "Mississippi": (34.3668, -89.5383),
    "Mississippi State": (33.4552, -88.7944),
    "Mississippi Valley State": (33.5186, -90.3446),
    "Missouri": (38.9404, -92.3277),
    "Missouri State": (37.2080, -93.2923),
    "Monmouth": (40.3468, -74.0824),
    "Montana": (46.8615, -113.9843),
    "Montana State": (45.6676, -111.0540),
    "Morehead State": (38.1864, -83.4327),
    "Morgan State": (39.3451, -76.5636),
    "Mount St. Mary's": (39.6543, -77.4644),
    "Murray State": (36.6165, -88.3178),
    "N.C. State": (35.7847, -78.6821),
    "Navy": (38.9807, -76.4843),
    "Nebraska": (40.8202, -96.7005),
    "Nebraska Omaha": (41.2586, -95.9345),
    "Nevada": (39.5441, -119.8164),
    "Nevada Las Vegas": (36.1085, -115.1432),
    "New Hampshire": (43.1345, -70.9289),
    "New Mexico": (35.0844, -106.6504),
    "New Mexico State": (32.2829, -106.7538),
    "New Orleans": (30.0687, -89.9288),
    "Niagara": (43.0945, -79.0369),
    "Nicholls State": (29.7966, -91.3480),
    "Norfolk State": (36.8468, -76.2694),
    "North Carolina": (35.9049, -79.0469),
    "North Carolina A&T": (36.0726, -79.7719),
    "North Carolina Central": (35.9740, -78.8986),
    "North Carolina Wilmington": (34.2257, -77.9440),
    "North Dakota": (47.9253, -97.0329),
    "North Dakota State": (46.8949, -96.8003),
    "North Florida": (30.2695, -81.5074),
    "North Texas": (33.2075, -97.1526),
    "Northeastern": (42.3398, -71.0892),
    "Northern Arizona": (35.1907, -111.6513),
    "Northern Colorado": (40.4069, -104.6944),
    "Northern Illinois": (41.9341, -88.7661),
    "Northern Iowa": (42.4839, -92.4577),
    "Northern Kentucky": (39.0329, -84.5184),
    "Northwestern": (42.0550, -87.6753),
    "Northwestern State": (31.7667, -93.0833),
    "Notre Dame": (41.7056, -86.2353),
    "Oakland": (42.6676, -83.2097),
    "Ohio": (39.3292, -82.1013),
    "Ohio State": (40.0067, -83.0305),
    "Oklahoma": (35.2059, -97.4457),
    "Oklahoma State": (36.1270, -97.0737),
    "Old Dominion": (36.8862, -76.3100),
    "Oral Roberts": (36.0522, -95.9525),
    "Oregon": (44.0448, -123.0726),
    "Oregon State": (44.5638, -123.2794),
    "Pacific": (37.7848, -122.1811),
    "Penn State": (40.7982, -77.8599),
    "Pennsylvania": (39.9526, -75.1652),
    "Pepperdine": (34.0416, -118.7096),
    "Pittsburgh": (40.4406, -79.9959),
    "Portland": (45.5152, -122.6784),
    "Portland State": (45.5118, -122.6860),
    "Prairie View": (30.0972, -95.6161),
    "Princeton": (40.3431, -74.6514),
    "Providence": (41.8240, -71.4128),
    "Purdue": (40.4237, -86.9212),
    "Quinnipiac": (41.4201, -72.8956),
    "Radford": (37.1318, -80.5764),
    "Rhode Island": (41.4901, -71.5263),
    "Rice": (29.7174, -95.4018),
    "Richmond": (37.5407, -77.4360),
    "Rider": (40.2795, -74.0043),
    "Robert Morris": (40.5219, -80.2109),
    "Rutgers": (40.5008, -74.4474),
    "Sacramento State": (38.5615, -121.4237),
    "Sacred Heart": (41.2230, -73.2413),
    "Saint Joseph's": (39.9951, -75.2399),
    "Saint Louis": (38.6270, -90.1994),
    "Saint Mary's": (37.8415, -122.1041),
    "Saint Peter's": (40.7245, -74.0722),
    "Sam Houston": (30.7144, -95.5508),
    "Samford": (33.4659, -86.7919),
    "San Diego": (32.7157, -117.1611),
    "San Diego State": (32.7758, -117.0713),
    "San Francisco": (37.7749, -122.4194),
    "San Jose State": (37.3352, -121.8811),
    "Santa Clara": (37.3496, -121.9390),
    "Savannah State": (32.0295, -81.0942),
    "Seattle": (47.6062, -122.3321),
    "Seton Hall": (40.7431, -74.2467),
    "Siena": (42.7142, -73.7522),
    "South Alabama": (30.6944, -88.0431),
    "South Carolina": (34.0007, -81.0348),
    "South Carolina State": (33.4970, -80.8497),
    "South Dakota": (43.5446, -96.7311),
    "South Dakota State": (44.3180, -96.7833),
    "South Florida": (28.0587, -82.4139),
    "Southeast Missouri State": (37.3106, -89.5309),
    "Southeastern Louisiana": (30.5191, -90.4771),
    "Southern": (30.5236, -91.1920),
    "Southern California": (34.0224, -118.2851),
    "Southern Illinois": (37.7091, -89.2239),
    "Southern Illinois Edwardsville": (38.7927, -89.9971),
    "Southern Methodist": (32.8412, -96.7845),
    "Southern Mississippi": (31.3271, -89.2903),
    "Southern Utah": (37.0965, -113.5684),
    "St. Bonaventure": (42.0789, -78.4758),
    "St. Francis (PA)": (40.4364, -80.0848),
    "St. John's": (40.7220, -73.7949),
    "Stanford": (37.4275, -122.1697),
    "Stephen F. Austin": (31.6099, -94.6501),
    "Stetson": (29.0356, -80.8973),
    "Stony Brook": (40.9120, -73.1224),
    "Syracuse": (43.0481, -76.1474),
    "Temple": (39.9818, -75.1550),
    "Tennessee": (35.9606, -83.9207),
    "Tennessee State": (36.1670, -86.7842),
    "Tennessee Tech": (36.1715, -85.5016),
    "Texas": (30.2849, -97.7341),
    "Texas A&M": (30.6185, -96.3365),
    "Texas A&M Corpus Christi": (27.7305, -97.3544),
    "Texas Arlington": (32.7319, -97.1143),
    "Texas Christian": (32.7098, -97.3625),
    "Texas El Paso": (31.7725, -106.5070),
    "Texas Rio Grande Valley": (26.1892, -98.2269),
    "Texas San Antonio": (29.4241, -98.4936),
    "Texas Southern": (29.7224, -95.3625),
    "Texas State": (29.8884, -97.9384),
    "Texas Tech": (33.5843, -101.8788),
    "Toledo": (41.6577, -83.6141),
    "Towson": (39.3927, -76.6122),
    "Troy": (31.7990, -85.9705),
    "Tulane": (29.9403, -90.1203),
    "Tulsa": (36.1539, -95.9928),
    "UAB": (33.5022, -86.8089),
    "UC Davis": (38.5382, -121.7617),
    "UC Irvine": (33.6405, -117.8443),
    "UC Riverside": (33.9737, -117.3281),
    "UC Santa Barbara": (34.4140, -119.8489),
    "UCF": (28.6024, -81.2001),
    "UCLA": (34.0689, -118.4452),
    "UMass": (42.4084, -71.1185),
    "UMass Lowell": (42.6403, -71.3220),
    "UMBC": (39.2547, -76.7141),
    "UNC Asheville": (35.6009, -82.5540),
    "UNC Greensboro": (36.0726, -79.7719),
    "UNC Wilmington": (34.2257, -77.9440),
    "UNLV": (36.1085, -115.1432),
    "USC": (34.0224, -118.2851),
    "USC Upstate": (34.9626, -81.9357),
    "UT Martin": (36.3418, -88.8529),
    "Utah": (40.7649, -111.8421),
    "Utah State": (41.7400, -111.8278),
    "Utah Valley": (40.2762, -111.7157),
    "Valparaiso": (41.4631, -87.0439),
    "Vanderbilt": (36.1447, -86.8027),
    "Vermont": (44.4779, -73.1965),
    "Villanova": (40.0379, -75.3433),
    "Virginia": (38.0336, -78.5080),
    "Virginia Commonwealth": (37.5483, -77.4528),
    "Virginia Military Institute": (37.7869, -79.4439),
    "Virginia Tech": (37.2284, -80.4234),
    "Wagner": (40.7457, -74.0257),
    "Wake Forest": (36.1355, -80.2792),
    "Washington": (47.6553, -122.3035),
    "Washington State": (46.7319, -117.1542),
    "Weber State": (41.1924, -111.9449),
    "West Virginia": (39.6480, -79.9694),
    "Western Carolina": (35.3082, -83.1843),
    "Western Illinois": (40.4782, -90.6868),
    "Western Kentucky": (36.9693, -86.4558),
    "Western Michigan": (42.2829, -85.6152),
    "Wichita State": (37.6922, -97.3375),
    "William & Mary": (37.2707, -76.7098),
    "Winthrop": (34.9399, -81.0298),
    "Wisconsin": (43.0766, -89.4125),
    "Wisconsin Milwaukee": (43.0389, -87.9065),
    "Wofford": (34.9626, -81.9357),
    "Wright State": (39.7800, -84.0633),
    "Wyoming": (41.3148, -105.5624),
    "Xavier": (39.1499, -84.4773),
    "Yale": (41.3163, -72.9223),
    "Youngstown State": (41.1028, -80.6463)
}


def get_school_coordinates(school_name: str) -> Optional[Dict[str, int]]:
    """
    Get game coordinates for a school.

    First tries to look up in the predefined SCHOOL_COORDINATES dict,
    then falls back to geocoding if available.

    Args:
        school_name: Name of the school

    Returns:
        Dict with 'x' and 'y' keys, or None if not found
    """
    # Try predefined coordinates first
    if school_name in SCHOOL_COORDINATES:
        lat, lng = SCHOOL_COORDINATES[school_name]
        return lat_lng_to_game_coords(lat, lng)

    # TODO: Add geocoding fallback here when requests is available
    logger.warning(f"No coordinates found for school: {school_name}")
    return None


def populate_ncaa_coordinates(ncaa_data_file: str = "src/hoopland/data/ncaa_team_data.json") -> None:
    """
    Populate coordinates for all NCAA schools in the data file.

    Args:
        ncaa_data_file: Path to the NCAA team data JSON file
    """
    import json

    # Load current data
    with open(ncaa_data_file, 'r') as f:
        data = json.load(f)

    updated_count = 0

    # Update coordinates for each school
    for school_key, school_data in data.items():
        school_name = school_data.get('school', '')
        current_coords = school_data.get('location', {})

        # Only update if coordinates are missing (x=0, y=0)
        if current_coords.get('x') == 0 and current_coords.get('y') == 0:
            coords = get_school_coordinates(school_name)
            if coords:
                school_data['location'] = coords
                updated_count += 1
                logger.info(f"Updated coordinates for {school_name}: {coords}")
            else:
                logger.warning(f"Could not find coordinates for {school_name}")

    # Save updated data
    with open(ncaa_data_file, 'w') as f:
        json.dump(data, f, indent=2)

    logger.info(f"Updated coordinates for {updated_count} schools")
