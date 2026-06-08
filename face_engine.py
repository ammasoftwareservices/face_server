import cv2
import mediapipe as mp
import numpy as np

_face_mesh = mp.solutions.face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
)


def _safe_crop(gray, points, margin=14):
    height, width = gray.shape
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    x1 = max(min(xs) - margin, 0)
    x2 = min(max(xs) + margin, width)
    y1 = max(min(ys) - margin, 0)
    y2 = min(max(ys) + margin, height)

    if x2 <= x1 or y2 <= y1:
        return None

    return gray[y1:y2, x1:x2]


def _fallback_eye_crop(gray):
    height, width = gray.shape
    y1 = int(height * 0.20)
    y2 = int(height * 0.52)
    x1 = int(width * 0.12)
    x2 = int(width * 0.88)
    return gray[y1:y2, x1:x2]


def _normalize_patch(patch, size=(64, 64)):
    patch = cv2.resize(patch, size)
    patch = cv2.equalizeHist(patch)
    patch = patch.astype("float32") / 255.0
    return patch.flatten()


def get_embedding(frame):
    """
    Eye-lens/iris-region embedding generator.

    The Flutter app verifies liveness with a blink before calling this endpoint.
    Here we use MediaPipe Face Mesh iris landmarks when available and fall back
    to the upper eye band, so the API keeps working on lower quality frames.
    """

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mesh = _face_mesh.process(rgb)

    left_eye = None
    right_eye = None
    if mesh.multi_face_landmarks:
        landmarks = mesh.multi_face_landmarks[0].landmark
        height, width = gray.shape

        def point(index):
            landmark = landmarks[index]
            return int(landmark.x * width), int(landmark.y * height)

        left_eye_indices = [33, 133, 159, 145, 468, 469, 470, 471, 472]
        right_eye_indices = [362, 263, 386, 374, 473, 474, 475, 476, 477]

        left_eye = _safe_crop(gray, [point(index) for index in left_eye_indices])
        right_eye = _safe_crop(gray, [point(index) for index in right_eye_indices])

    if left_eye is not None and right_eye is not None:
        patches = [_normalize_patch(left_eye), _normalize_patch(right_eye)]
    else:
        # Always return the same vector length. One-eye captures used to create
        # a shorter vector, which made later verification fail by shape mismatch.
        patches = [_normalize_patch(_fallback_eye_crop(gray), size=(128, 64))]

    return np.concatenate(patches).astype("float32")


def compare_embeddings(emb1, emb2, threshold=0.72):
    """
    Uses cosine similarity.
    Returns True if match, False otherwise.
    """

    emb1 = np.array(emb1, dtype=np.float32)
    emb2 = np.array(emb2, dtype=np.float32)

    if emb1.size == 0 or emb2.size == 0:
        return False
    if emb1.shape != emb2.shape:
        size = min(emb1.size, emb2.size)
        if size < 1024:
            return False
        emb1 = emb1[:size]
        emb2 = emb2[:size]

    norm1 = np.linalg.norm(emb1)
    norm2 = np.linalg.norm(emb2)
    if norm1 == 0 or norm2 == 0:
        return False

    emb1 = emb1 / norm1
    emb2 = emb2 / norm2
    similarity = np.dot(emb1, emb2)

    return similarity > threshold
