"""
Facial Landmark Detection Module

Uses MediaPipe Face Mesh to detect facial landmarks for more accurate
appearance detection. Key features:
- Ear visibility detection (covered ears = longer hair)
- Precise chin region (for facial hair detection)  
- Eyebrow positions (for forehead/hair boundary)

MediaPipe Face Mesh provides 468 landmarks. Key landmark indices:
- Ears: 234 (left), 454 (right) and surrounding points
- Chin: Points along jawline (0-16 region)
- Eyebrows: Points in eyebrow region
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import cv2
    import mediapipe as mp
    import numpy as np

    MEDIAPIPE_AVAILABLE = True
except ImportError as e:
    MEDIAPIPE_AVAILABLE = False
    logger.warning(f"MediaPipe not available: {e}")


# MediaPipe Face Mesh landmark indices
# Reference: https://github.com/google/mediapipe/blob/master/mediapipe/modules/face_geometry/data/canonical_face_model_uv_visualization.png

# Left ear region landmarks
LEFT_EAR_INDICES = [234, 127, 162, 21, 54, 103, 67, 109, 10]

# Right ear region landmarks
RIGHT_EAR_INDICES = [454, 356, 389, 251, 284, 332, 297, 338, 10]

# Chin/jawline landmarks (lower face)
CHIN_INDICES = [
    152,
    377,
    400,
    378,
    379,
    365,
    397,
    288,
    361,
    323,
    454,
    356,
    389,
    251,
    284,
    332,
    297,
    338,
    10,
    109,
    67,
    103,
    54,
    21,
    162,
    127,
    234,
    93,
    132,
    58,
    172,
    136,
    150,
    149,
    176,
    148,
]

# Forehead boundary (eyebrow tops)
LEFT_EYEBROW_TOP = [70, 63, 105, 66, 107]
RIGHT_EYEBROW_TOP = [336, 296, 334, 293, 300]

# Eye landmarks for reference
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]


class FaceLandmarkDetector:
    """
    Detects facial landmarks using MediaPipe Face Mesh.

    Provides methods for:
    - Full face mesh detection (468 landmarks)
    - Ear visibility checking
    - Chin region extraction
    - Forehead boundary detection
    """

    def __init__(
        self, static_image_mode: bool = True, min_detection_confidence: float = 0.5
    ):
        """
        Initialize the face landmark detector.

        Args:
            static_image_mode: Whether to treat images as static (True for photos)
            min_detection_confidence: Minimum confidence for face detection
        """
        if not MEDIAPIPE_AVAILABLE:
            raise RuntimeError("MediaPipe is not installed")

        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=static_image_mode,
            max_num_faces=1,
            refine_landmarks=True,  # Enables iris landmarks
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=0.5,
        )

    def detect_landmarks(self, img: np.ndarray) -> Optional[np.ndarray]:
        """
        Detect facial landmarks in an image.

        Args:
            img: BGR image as numpy array

        Returns:
            Array of shape (468, 2) with (x, y) coordinates for each landmark,
            or None if no face detected.
        """
        # Convert BGR to RGB
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        results = self.face_mesh.process(rgb_img)

        if not results.multi_face_landmarks:
            return None

        # Get first face
        face_landmarks = results.multi_face_landmarks[0]

        h, w = img.shape[:2]

        # Convert normalized coordinates to pixel coordinates
        landmarks = np.array(
            [[int(lm.x * w), int(lm.y * h)] for lm in face_landmarks.landmark]
        )

        return landmarks

    def detect_ear_visibility(
        self, landmarks: np.ndarray, img_width: int
    ) -> tuple[bool, bool]:
        """
        Check if ears are visible (not covered by hair).

        Ears are considered visible if:
        1. Ear landmarks are near the edge of the face silhouette
        2. Ear x-coordinates extend beyond the face center

        Args:
            landmarks: Array of shape (468, 2) with landmark coordinates
            img_width: Width of the image

        Returns:
            (left_ear_visible, right_ear_visible)
        """
        # Get ear landmark positions
        left_ear_pts = landmarks[LEFT_EAR_INDICES]
        right_ear_pts = landmarks[RIGHT_EAR_INDICES]

        # Get face center (using nose tip as reference)
        nose_tip = landmarks[1]  # Nose tip landmark
        face_center_x = nose_tip[0]

        # Get face width from cheek landmarks
        left_cheek = landmarks[234]  # Left ear anchor
        right_cheek = landmarks[454]  # Right ear anchor
        face_width = abs(right_cheek[0] - left_cheek[0])

        # Ears are visible if they extend beyond a certain threshold from face center
        # If hair covers ears, the ear landmarks will be closer to face center

        # Left ear: should be significantly left of face center
        left_ear_x = np.mean(left_ear_pts[:, 0])
        left_ear_visible = (face_center_x - left_ear_x) > face_width * 0.35

        # Right ear: should be significantly right of face center
        right_ear_x = np.mean(right_ear_pts[:, 0])
        right_ear_visible = (right_ear_x - face_center_x) > face_width * 0.35

        # Also check if ears are near image edges (another indicator of visibility)
        edge_threshold = img_width * 0.15
        left_near_edge = left_ear_x < edge_threshold
        right_near_edge = right_ear_x > (img_width - edge_threshold)

        # Final determination: visible if position is correct OR near edge
        left_visible = left_ear_visible or left_near_edge
        right_visible = right_ear_visible or right_near_edge

        return left_visible, right_visible

    def get_chin_polygon(self, landmarks: np.ndarray) -> np.ndarray:
        """
        Get the chin/lower face polygon for facial hair detection.

        Args:
            landmarks: Array of shape (468, 2) with landmark coordinates

        Returns:
            Array of points forming chin polygon
        """
        # Get chin landmarks
        chin_pts = landmarks[CHIN_INDICES]

        # Sort by angle from center to form proper polygon
        center = np.mean(chin_pts, axis=0)
        angles = np.arctan2(chin_pts[:, 1] - center[1], chin_pts[:, 0] - center[0])
        sorted_indices = np.argsort(angles)

        return chin_pts[sorted_indices]

    def get_forehead_boundary(self, landmarks: np.ndarray) -> int:
        """
        Get the Y coordinate of the forehead/hair boundary.

        This is the top of the eyebrows, which represents where
        hair typically begins.

        Args:
            landmarks: Array of shape (468, 2) with landmark coordinates

        Returns:
            Y coordinate of forehead boundary
        """
        left_brow = landmarks[LEFT_EYEBROW_TOP]
        right_brow = landmarks[RIGHT_EYEBROW_TOP]

        # Hair boundary is above the highest eyebrow point
        all_brow_pts = np.vstack([left_brow, right_brow])
        min_y = np.min(all_brow_pts[:, 1])

        return int(min_y)

    def get_face_bounds(self, landmarks: np.ndarray) -> tuple[int, int, int, int]:
        """
        Get bounding box of the face.

        Args:
            landmarks: Array of shape (468, 2) with landmark coordinates

        Returns:
            (x_min, y_min, x_max, y_max)
        """
        x_min = int(np.min(landmarks[:, 0]))
        y_min = int(np.min(landmarks[:, 1]))
        x_max = int(np.max(landmarks[:, 0]))
        y_max = int(np.max(landmarks[:, 1]))

        return x_min, y_min, x_max, y_max

    def close(self):
        """Release resources."""
        self.face_mesh.close()


# Module-level singleton for efficiency
_detector: Optional[FaceLandmarkDetector] = None


def get_detector() -> Optional[FaceLandmarkDetector]:
    """
    Get or create the global face landmark detector.

    Returns:
        FaceLandmarkDetector instance, or None if MediaPipe unavailable
    """
    global _detector

    if not MEDIAPIPE_AVAILABLE:
        return None

    if _detector is None:
        try:
            _detector = FaceLandmarkDetector()
        except Exception as e:
            logger.error(f"Failed to initialize face detector: {e}")
            return None

    return _detector


def detect_landmarks(img: np.ndarray) -> Optional[np.ndarray]:
    """
    Convenience function to detect landmarks.

    Args:
        img: BGR image

    Returns:
        Landmarks array or None
    """
    detector = get_detector()
    if detector is None:
        return None
    return detector.detect_landmarks(img)


def detect_ear_visibility(img: np.ndarray) -> tuple[bool, bool]:
    """
    Convenience function to check ear visibility.

    Args:
        img: BGR image

    Returns:
        (left_visible, right_visible), defaults to (True, True) if detection fails
    """
    detector = get_detector()
    if detector is None:
        return True, True  # Fallback: assume ears visible

    landmarks = detector.detect_landmarks(img)
    if landmarks is None:
        return True, True

    h, w = img.shape[:2]
    return detector.detect_ear_visibility(landmarks, w)


def get_forehead_boundary(img: np.ndarray) -> Optional[int]:
    """
    Convenience function to get forehead boundary.

    Args:
        img: BGR image

    Returns:
        Y coordinate of forehead boundary, or None if detection fails
    """
    detector = get_detector()
    if detector is None:
        return None

    landmarks = detector.detect_landmarks(img)
    if landmarks is None:
        return None

    return detector.get_forehead_boundary(landmarks)


def get_chin_polygon(img: np.ndarray) -> Optional[np.ndarray]:
    """
    Convenience function to get chin polygon.

    Args:
        img: BGR image

    Returns:
        Array of chin polygon points, or None if detection fails
    """
    detector = get_detector()
    if detector is None:
        return None

    landmarks = detector.detect_landmarks(img)
    if landmarks is None:
        return None

    return detector.get_chin_polygon(landmarks)
