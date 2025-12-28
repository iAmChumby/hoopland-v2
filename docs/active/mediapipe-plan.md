---
name: MediaPipe 0.10+ Migration
overview: Migrate the face landmark detection code from the deprecated MediaPipe solutions API to the new MediaPipe 0.10+ tasks API to resolve the "module 'mediapipe' has no attribute 'solutions'" error.
todos:
  - id: download-model
    content: Download face_landmarker.task model file from Google storage
    status: pending
  - id: create-models-dir
    content: Create src/hoopland/cv/models/ directory
    status: pending
  - id: update-imports
    content: Update imports in face_landmarks.py to use new tasks API
    status: pending
  - id: update-initialization
    content: Update FaceLandmarkDetector.__init__ for new API
    status: pending
  - id: update-detect-method
    content: Update detect_landmarks method to use new detect() API
    status: pending
  - id: update-close-method
    content: Update close() method to use face_landmarker.close()
    status: pending
  - id: update-requirements
    content: Add mediapipe>=0.10.0 to requirements.txt
    status: pending
  - id: test-migration
    content: Run tests to verify migration works correctly
    status: pending
  - id: update-readme
    content: Update README.md to mention MediaPipe for face landmark detection
    status: pending
  - id: update-spec-doc
    content: Update docs/spec.md CV section to document MediaPipe usage
    status: pending
  - id: update-architecture-doc
    content: Update docs/static/architecture.md CV Engine section
    status: pending
  - id: update-design-doc
    content: Update docs/static/design.md Appearance Logic section
    status: pending
  - id: archive-plan-doc
    content: Move docs/active/mediapipe-plan.md to completed/archived status
    status: pending
---

# MediaPipe 0.10+ Migration Plan

## Problem Summary

MediaPipe 0.10.31 is installed but the code uses the deprecated `mp.solutions` API which was removed in 0.10+. The new API uses `mediapipe.tasks.python.vision` with a different structure and requires a model file.

## Key Changes Required

### 1. Download Face Landmarker Model

The new API requires a `.task` model file. Download from:

```javascript
https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task
```

Store in: `src/hoopland/cv/models/face_landmarker.task` (create models directory)Update [pyproject.toml](pyproject.toml) or add to `.gitignore` if model is large.

### 2. Update [src/hoopland/cv/face_landmarks.py](src/hoopland/cv/face_landmarks.py)

#### Import Changes

**OLD API:**

```python
import mediapipe as mp
self.mp_face_mesh = mp.solutions.face_mesh
```

**NEW API:**

```python
from mediapipe.tasks import python as mp_tasks
from mediapipe.tasks.python import vision as mp_vision
from mediapipe.python._framework_bindings import image as mp_image
```



#### Initialization Changes

**OLD API:**

```python
self.mp_face_mesh = mp.solutions.face_mesh
self.face_mesh = self.mp_face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5
)
```

**NEW API:**

```python
base_options = mp_tasks.BaseOptions(
    model_asset_path=os.path.join(
        os.path.dirname(__file__), 
        'models', 
        'face_landmarker.task'
    )
)
options = mp_vision.FaceLandmarkerOptions(
    base_options=base_options,
    running_mode=mp_vision.RunningMode.IMAGE,
    num_faces=1,
    min_face_detection_confidence=0.5,
    min_face_presence_confidence=0.5,
    output_face_blendshapes=False,
    output_facial_transformation_matrixes=False
)
self.face_landmarker = mp_vision.FaceLandmarker.create_from_options(options)
```



#### Detection Method Changes

**OLD API:**

```python
rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
results = self.face_mesh.process(rgb_img)
if results.multi_face_landmarks:
    face_landmarks = results.multi_face_landmarks[0]
```

**NEW API:**

```python
rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
mp_img = mp_image.Image(image_format=mp_image.ImageFormat.SRGB, data=rgb_img)
results = self.face_landmarker.detect(mp_img)
if results.face_landmarks:
    face_landmarks = results.face_landmarks[0]
```



#### Landmark Coordinate Extraction

**OLD API:**

```python
landmarks = np.array(
    [[int(lm.x * w), int(lm.y * h)] for lm in face_landmarks.landmark]
)
```

**NEW API:**

```python
landmarks = np.array(
    [[int(lm.x * w), int(lm.y * h)] for lm in face_landmarks]
)
```

Note: Same structure, but `face_landmarks` is already a list in the new API.

#### Cleanup Method

**OLD API:**

```python
self.face_mesh.close()
```

**NEW API:**

```python
self.face_landmarker.close()
```



### 3. Update Landmark Indices

The landmark indices (468 points) remain the same:

- `LEFT_EAR_INDICES = [234, 127, 162, ...]`
- `RIGHT_EAR_INDICES = [454, 356, 389, ...]`
- `CHIN_INDICES = [152, 377, 400, ...]`
- etc.

No changes needed for these constants.

### 4. Update [requirements.txt](requirements.txt)

Add explicit MediaPipe version constraint:

```javascript
mediapipe>=0.10.0
```



### 5. Update Tests in [tests/unit/test_appearance.py](tests/unit/test_appearance.py)

Update the test that checks for MediaPipe availability:

```python
def test_mediapipe_available(self):
    from hoopland.cv import face_landmarks
    # Check new API availability
    assert face_landmarks.MEDIAPIPE_AVAILABLE is True
```



### 6. Error Handling

Keep the existing graceful fallback behavior - if MediaPipe fails to initialize, appearance analysis continues without landmark detection.

## API Comparison Summary

| Aspect | Old API | New API ||--------|---------|---------|| Module | `mp.solutions.face_mesh` | `mp_vision.FaceLandmarker` || Model | Built-in | External `.task` file required || Initialization | `FaceMesh()` constructor | `create_from_options(options)` || Detection | `process(image)` | `detect(mp_image)` || Results | `multi_face_landmarks[0].landmark` | `face_landmarks[0]` || Image Input | NumPy array (RGB) | `mp_image.Image` wrapper |

## Testing Strategy

1. Run existing unit tests to verify no regressions
2. Test with a known player image to verify landmark detection works
3. Verify ear visibility, chin polygon, and forehead boundary detection
4. Ensure graceful fallback when model file is missing

## Documentation Updates

### 1. Update [README.md](README.md)

**Current (Line 8):**
```markdown
- **Auto-Appearance**: Uses Computer Vision (OpenCV) to automatically determine player skin tone and hair color from headshots.
```

**Updated:**
```markdown
- **Auto-Appearance**: Uses Computer Vision (OpenCV + MediaPipe) to automatically determine player appearance attributes including skin tone, hair style, facial hair, and accessories from headshots. MediaPipe Face Landmarker provides precise facial landmark detection for improved accuracy.
```

**Current (Line 17):**
```markdown
*Note: Requires `opencv-python-headless`.*
```

**Updated:**
```markdown
*Note: Requires `opencv-python-headless` and `mediapipe>=0.10.0`.*
```

### 2. Update [docs/spec.md](docs/spec.md)

**Section 4 - Computer Vision (CV) Logic (Lines 67-89)**

Add new subsection after "Map:" line:

```markdown
### Facial Landmark Detection (MediaPipe)

**Library**: MediaPipe Face Landmarker (v0.10+)

**Model**: `face_landmarker.task` (float16, stored in `src/hoopland/cv/models/`)

**Purpose**: Detects 468 facial landmarks to enable:
- Ear visibility detection (for hair length estimation)
- Precise chin region detection (for facial hair analysis)
- Forehead boundary detection (for hair/forehead boundary)

**Implementation**:
- Uses MediaPipe Tasks API (`mediapipe.tasks.python.vision.FaceLandmarker`)
- Processes images in IMAGE running mode
- Falls back gracefully if detection fails or model is unavailable
- Landmark indices remain consistent with MediaPipe Face Mesh standard (468 points)

**Key Landmarks**:
- Left ear: indices [234, 127, 162, 21, 54, 103, 67, 109, 10]
- Right ear: indices [454, 356, 389, 251, 284, 332, 297, 338, 10]
- Chin/jawline: indices [152, 377, 400, ...] (full list in code)
- Eyebrow tops: Left [70, 63, 105, 66, 107], Right [336, 296, 334, 293, 300]
```

### 3. Update [docs/static/architecture.md](docs/static/architecture.md)

**Section: Engines (Lines 18-19)**

**Current:**
```markdown
- **CV Engine**: Analyzes player headshots to determine skin tone and hair color.
```

**Updated:**
```markdown
- **CV Engine**: Analyzes player headshots using OpenCV and MediaPipe to determine:
  - Skin tone (1-10 scale)
  - Hair style (0-130+ indexed styles)
  - Facial hair (0-24 indexed styles)
  - Accessories (0-16 indexed styles)
  - Uses MediaPipe Face Landmarker (v0.10+) for precise facial feature detection
  - Falls back to basic analysis if MediaPipe is unavailable
```

### 4. Update [docs/static/design.md](docs/static/design.md)

**Section: Appearance Logic (Lines 13-16)**

**Current:**
```markdown
## Appearance Logic
We use OpenCV to detect skin tone to avoid manual entry.
- **Algorithm**: YCrCb color space analysis on the center crop of the headshot.
- **Fallback**: Default to medium skin tone if image fetch fails.
```

**Updated:**
```markdown
## Appearance Logic
We use OpenCV and MediaPipe for comprehensive appearance detection.

### Skin Tone Detection
- **Algorithm**: YCrCb color space analysis on skin-masked regions of the headshot
- **Color Space**: YCrCb (better for skin detection than RGB)
- **Mapping**: Average RGB → Hoop Land Skin Code (1-10) via similarity matching

### Facial Landmark Detection
- **Library**: MediaPipe Face Landmarker v0.10+ (Tasks API)
- **Model**: `face_landmarker.task` (468 landmark points)
- **Features**:
  - Ear visibility detection → Hair length estimation
  - Chin polygon extraction → Precise facial hair detection
  - Forehead boundary detection → Hair/forehead separation
- **Fallback**: Basic image analysis if MediaPipe unavailable or detection fails

### Hair & Accessory Detection
- **Method**: Color histogram analysis in specific facial regions
- **Enhanced by**: MediaPipe landmarks for precise region boundaries
- **Output**: Indexed styles matching Hoopland's appearance mapping
```

### 5. Archive [docs/active/mediapipe-plan.md](docs/active/mediapipe-plan.md)

After implementation is complete, move this file to indicate completion:
- Option A: Move to `docs/completed/mediapipe-migration.md`
- Option B: Add a "COMPLETED" prefix: `docs/active/COMPLETED-mediapipe-plan.md`
- Option C: Delete if content is fully captured in git history

Recommended: **Option A** - Create `docs/completed/` directory and move there with completion date.

## Files to Modify

### Code Files
1. [src/hoopland/cv/face_landmarks.py](src/hoopland/cv/face_landmarks.py) - Main migration
2. [requirements.txt](requirements.txt) - Add version constraint
3. [pyproject.toml](pyproject.toml) - Update MediaPipe dependency
4. [tests/unit/test_appearance.py](tests/unit/test_appearance.py) - Update tests

### Documentation Files
5. [README.md](README.md) - Update CV feature description
6. [docs/spec.md](docs/spec.md) - Add MediaPipe section to CV Logic
7. [docs/static/architecture.md](docs/static/architecture.md) - Expand CV Engine description
8. [docs/static/design.md](docs/static/design.md) - Expand Appearance Logic section
9. [docs/active/mediapipe-plan.md](docs/active/mediapipe-plan.md) - Archive after completion

### New Files/Directories
10. `src/hoopland/cv/models/` - Directory for model files
11. `src/hoopland/cv/models/face_landmarker.task` - MediaPipe model file
12. `docs/completed/` - Directory for completed plans (optional)