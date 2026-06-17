import cv2
import numpy as np
from insightface.app import FaceAnalysis

# Load model once at startup
_face_app = FaceAnalysis(
    name="buffalo_l",
    providers=["CPUExecutionProvider"]
)

_face_app.prepare(
    ctx_id=0,
    det_size=(640, 640)
)


def get_embedding(frame):
    """
    Generate a 512-dimensional face embedding.
    """

    if frame is None:
        raise ValueError("Invalid frame")

    if len(frame.shape) != 3:
        raise ValueError("Invalid image format")

    faces = _face_app.get(frame)

    if not faces:
        raise ValueError("No face detected")

    # Largest face
    face = max(
        faces,
        key=lambda f: (
            (f.bbox[2] - f.bbox[0]) *
            (f.bbox[3] - f.bbox[1])
        )
    )

    embedding = face.normed_embedding

    if embedding is None:
        raise ValueError("Face embedding generation failed")

    return embedding.astype(np.float32)


def cosine_similarity(emb1, emb2):
    emb1 = np.array(emb1, dtype=np.float32)
    emb2 = np.array(emb2, dtype=np.float32)

    if emb1.size == 0 or emb2.size == 0:
        return 0.0

    if emb1.shape != emb2.shape:
        return 0.0

    norm1 = np.linalg.norm(emb1)
    norm2 = np.linalg.norm(emb2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    emb1 = emb1 / norm1
    emb2 = emb2 / norm2

    return float(np.dot(emb1, emb2))


def compare_embeddings(
    emb1,
    emb2,
    threshold=0.55
):
    """
    Returns True if same face.
    """

    similarity = cosine_similarity(
        emb1,
        emb2
    )

    print(
        f"Face Similarity = {similarity:.4f}"
    )

    return similarity >= threshold
