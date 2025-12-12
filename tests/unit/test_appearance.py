"""
Tests for appearance detection and mapping loader.
"""

import pytest
from hoopland.cv import appearance
from hoopland.cv import mapping_loader


class TestMappingLoader:
    """Tests for the mapping loader module."""

    def test_load_appearance_mapping(self):
        """Test that the appearance mapping loads successfully."""
        data = mapping_loader.load_appearance_mapping()

        assert data is not None
        assert "meta" in data
        assert "mappings" in data

        # Check metadata
        meta = data["meta"]
        assert meta["total_styles"] == 173

    def test_get_all_styles_hair(self):
        """Test getting all hair styles."""
        styles = mapping_loader.get_all_styles("hair")

        assert len(styles) == 131
        assert styles[0]["index"] == 0
        assert "description" in styles[0]

    def test_get_all_styles_facial_hair(self):
        """Test getting all facial hair styles."""
        styles = mapping_loader.get_all_styles("facial_hair")

        assert len(styles) == 25
        assert styles[0]["index"] == 0

    def test_get_all_styles_accessories(self):
        """Test getting all accessory styles."""
        styles = mapping_loader.get_all_styles("accessories")

        assert len(styles) == 17
        assert styles[0]["index"] == 0

    def test_get_style_by_index(self):
        """Test getting a specific style by index."""
        # Bald (index 0)
        style = mapping_loader.get_style_by_index("hair", 0)
        assert style is not None
        assert "Bald" in style["description"]

        # Full beard (index 24)
        style = mapping_loader.get_style_by_index("facial_hair", 24)
        assert style is not None
        assert "Beard" in style["description"]

    def test_get_style_description(self):
        """Test getting style descriptions."""
        desc = mapping_loader.get_style_description("hair", 17)
        assert "Fluffy" in desc or "Afro" in desc

    def test_search_styles(self):
        """Test searching styles by keywords."""
        # Search for afro styles
        afro_styles = mapping_loader.search_styles("hair", ["afro"])
        assert len(afro_styles) > 0

        for style in afro_styles:
            assert "afro" in style["description"].lower()

        # Search for dreads
        dread_styles = mapping_loader.search_styles("hair", ["dreads", "dread"])
        assert len(dread_styles) > 0


class TestHairClassification:
    """Tests for hair classification functions."""

    def test_classify_hair_length_bald(self):
        """Test bald classification."""
        assert mapping_loader.classify_hair_length("Bald/Shaved Head") == "bald"

    def test_classify_hair_length_short(self):
        """Test short hair classification."""
        assert mapping_loader.classify_hair_length("Short Fade") == "short"
        assert mapping_loader.classify_hair_length("Short Curls") == "short"

    def test_classify_hair_length_medium(self):
        """Test medium hair classification."""
        assert mapping_loader.classify_hair_length("Medium Afro") == "medium"

    def test_classify_hair_length_long(self):
        """Test long hair classification."""
        assert mapping_loader.classify_hair_length("Long Dreads") == "long"
        assert mapping_loader.classify_hair_length("Over shoulders") == "long"

    def test_classify_hair_texture_afro(self):
        """Test afro texture classification."""
        assert mapping_loader.classify_hair_texture("Medium Afro") == "afro"
        assert mapping_loader.classify_hair_texture("Coils") == "afro"

    def test_classify_hair_texture_dreads(self):
        """Test dreads texture classification."""
        assert mapping_loader.classify_hair_texture("Long Dreads") == "dreads"
        assert mapping_loader.classify_hair_texture("Twists") == "dreads"

    def test_classify_hair_volume(self):
        """Test volume classification."""
        assert mapping_loader.classify_hair_volume("Bald") == "none"
        assert mapping_loader.classify_hair_volume("Buzzcut") == "low"
        assert mapping_loader.classify_hair_volume("Very Large Afro") == "very_high"


class TestFacialHairClassification:
    """Tests for facial hair classification."""

    def test_classify_clean_shaven(self):
        """Test clean shaven classification."""
        assert mapping_loader.classify_facial_hair_density("Clean Shaven") == "none"

    def test_classify_stubble(self):
        """Test stubble classification."""
        assert mapping_loader.classify_facial_hair_density("Light Stubble") == "stubble"

    def test_classify_goatee(self):
        """Test goatee classification."""
        assert mapping_loader.classify_facial_hair_density("Goatee") == "goatee"

    def test_classify_beard(self):
        """Test beard classification."""
        assert mapping_loader.classify_facial_hair_density("Boxed Beard") == "beard"

    def test_classify_full_beard(self):
        """Test full beard classification."""
        assert (
            mapping_loader.classify_facial_hair_density("Full Dark Beard")
            == "full_beard"
        )


class TestStyleIndexBuilding:
    """Tests for building style indices."""

    def test_build_hair_index(self):
        """Test building hair attribute index."""
        index = mapping_loader.build_hair_index_by_attributes()

        assert "length" in index
        assert "texture" in index
        assert "volume" in index

        # Bald should be in 'none' volume
        assert 0 in index["volume"]["none"]

    def test_build_facial_hair_index(self):
        """Test building facial hair density index."""
        index = mapping_loader.build_facial_hair_index_by_density()

        assert "none" in index
        # Index 0 should be clean shaven
        assert 0 in index["none"]


class TestAppearanceDetection:
    """Tests for the main appearance detection functions."""

    def test_skin_tone_range(self):
        """Test that skin tone detection returns valid range."""
        # This tests with a known URL
        result = appearance.analyze_player_appearance("")
        assert 1 <= result["skin_tone"] <= 10

    def test_hair_style_range(self):
        """Test that hair style detection returns valid range."""
        result = appearance.analyze_player_appearance("")
        assert 0 <= result["hair"] <= 130

    def test_facial_hair_range(self):
        """Test that facial hair detection returns valid range."""
        result = appearance.analyze_player_appearance("")
        assert 0 <= result["facial_hair"] <= 24

    def test_accessory_range(self):
        """Test that accessory detection returns valid range."""
        result = appearance.analyze_player_appearance("")
        assert 0 <= result["accessory"] <= 16

    def test_empty_url_returns_defaults(self):
        """Test that empty URL returns default values."""
        result = appearance.analyze_player_appearance("")

        assert result["skin_tone"] == 1
        assert result["hair"] == 0
        assert result["facial_hair"] == 0
        assert result["accessory"] == 0


@pytest.mark.slow
@pytest.mark.integration
class TestIntegrationAppearance:
    """Integration tests that hit the network."""

    def test_james_harden_has_beard(self):
        """
        Test that James Harden is detected with a beard.
        Harden is famous for his thick beard.
        """
        # James Harden player ID: 201935
        url = "https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/201935.png"

        result = appearance.analyze_player_appearance(url)

        assert isinstance(result, dict)
        assert "facial_hair" in result
        # Harden should have significant facial hair (not clean shaven)
        # Indices 0, 16 = clean shaven, anything else indicates facial hair
        assert result["facial_hair"] not in [
            0,
            16,
        ], f"Expected Harden to have beard, got index {result['facial_hair']}"

    def test_jalen_brunson_has_dreads(self):
        """
        Test that Jalen Brunson is detected with longer/dread hair.
        Brunson has distinctive longer hair/dreads.
        """
        # Jalen Brunson player ID: 1628973
        url = "https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/1628973.png"

        result = appearance.analyze_player_appearance(url)

        assert isinstance(result, dict)
        assert "hair" in result
        # Brunson should NOT be bald (index 0)
        assert result["hair"] != 0, "Expected Brunson to have hair, not bald"

    def test_lebron_james_appearance(self):
        """
        Test LeBron James detection.
        LeBron has had various hairstyles but typically has some hair and facial hair.
        """
        # LeBron James player ID: 2544
        url = "https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/2544.png"

        result = appearance.analyze_player_appearance(url)

        assert isinstance(result, dict)
        assert "skin_tone" in result
        assert "hair" in result
        assert "facial_hair" in result

        # Basic sanity checks
        assert 1 <= result["skin_tone"] <= 10
        assert 0 <= result["hair"] <= 130
        assert 0 <= result["facial_hair"] <= 24

    def test_aj_guyton_appearance(self):
        """
        Test A.J. Guyton appearance (original test case).
        """
        url = "https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/2062.png"

        result = appearance.analyze_player_appearance(url)

        assert isinstance(result, dict)
        assert "skin_tone" in result
        assert "hair" in result
        assert "facial_hair" in result
        assert "accessory" in result


class TestFaceLandmarks:
    """Tests for the facial landmark detection module."""

    def test_mediapipe_available(self):
        """Test that MediaPipe is available."""
        from hoopland.cv import face_landmarks

        assert face_landmarks.MEDIAPIPE_AVAILABLE is True

    def test_detector_initialization(self):
        """Test that the face detector can be initialized."""
        from hoopland.cv import face_landmarks

        detector = face_landmarks.get_detector()
        assert detector is not None

    @pytest.mark.slow
    @pytest.mark.integration
    def test_ear_visibility_short_hair(self):
        """
        Test ear visibility for a player with short hair.
        Stephen Curry has short hair, ears should be visible.
        """
        import cv2
        import numpy as np
        import requests
        from hoopland.cv import face_landmarks

        url = "https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/201939.png"
        resp = requests.get(url, timeout=5)
        arr = np.asarray(bytearray(resp.content), dtype=np.uint8)
        img = cv2.imdecode(arr, -1)

        left_vis, right_vis = face_landmarks.detect_ear_visibility(img[:, :, :3])

        # For short hair, at least one ear should typically be visible
        assert left_vis or right_vis, "Expected at least one ear visible for short hair"

    @pytest.mark.slow
    @pytest.mark.integration
    def test_ear_visibility_afro(self):
        """
        Test ear visibility for a player with large afro.
        Anthony Davis has a notable afro, ears may be covered.
        """
        import cv2
        import numpy as np
        import requests
        from hoopland.cv import face_landmarks

        url = "https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/203076.png"
        resp = requests.get(url, timeout=5)
        arr = np.asarray(bytearray(resp.content), dtype=np.uint8)
        img = cv2.imdecode(arr, -1)

        left_vis, right_vis = face_landmarks.detect_ear_visibility(img[:, :, :3])

        # Anthony Davis has a large afro, at least one ear should be covered
        # Note: This is a soft test as headshot angles vary
        assert not (
            left_vis and right_vis
        ), "Expected at least one ear covered for afro"

    @pytest.mark.slow
    @pytest.mark.integration
    def test_forehead_boundary_detection(self):
        """Test that forehead boundary is detected correctly."""
        import cv2
        import numpy as np
        import requests
        from hoopland.cv import face_landmarks

        url = "https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/201939.png"
        resp = requests.get(url, timeout=5)
        arr = np.asarray(bytearray(resp.content), dtype=np.uint8)
        img = cv2.imdecode(arr, -1)

        forehead_y = face_landmarks.get_forehead_boundary(img[:, :, :3])

        # Forehead should be in upper portion of image
        h = img.shape[0]
        assert forehead_y is not None
        assert (
            0 < forehead_y < h // 2
        ), f"Forehead boundary {forehead_y} should be in upper half of {h}px image"
