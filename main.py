from fastapi import FastAPI, File, Form, HTTPException, UploadFile
import cv2
import json
import numpy as np

from face_engine import compare_embeddings, get_embedding
from mssql_sync import (
    SyncNotConfiguredError,
    get_next_school_id,
    login_and_get_bundle,
    sync_event_to_mssql,
    test_connection,
)

app = FastAPI(title="AttendancePro Face API", version="1.1.0")


@app.get("/")
def home():
    return {"status": "running", "service": "attendancepro-face-api"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/db-health")
def db_health():
    try:
        return {"status": "connected", **test_connection()}
    except SyncNotConfiguredError as error:
        raise HTTPException(status_code=503, detail=str(error))
    except Exception as error:
        print("DB HEALTH ERROR:", error)
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/next-school-id")
def next_school_id():
    try:
        return {"school_id": get_next_school_id()}
    except SyncNotConfiguredError as error:
        raise HTTPException(status_code=503, detail=str(error))
    except Exception as error:
        print("NEXT SCHOOL ID ERROR:", error)
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/verify-face")
async def verify_face(
    image: UploadFile = File(...),
    stored_embedding: str = Form(...),
):
    try:
        saved_embedding = np.array(json.loads(stored_embedding), dtype=np.float32)
        frame = await _read_frame(image)
        live_embedding = get_embedding(frame)
        match = bool(compare_embeddings(saved_embedding, live_embedding))

        return {
            "match": match,
            "success": match,
            "message": "Eye lens matched." if match else "Eye lens did not match.",
        }
    except Exception as error:
        print("ERROR:", error)
        return {
            "match": False,
            "success": False,
            "message": f"Server error: {error}",
        }


@app.post("/identify-face")
async def identify_face(
    image: UploadFile = File(...),
    candidates: str = Form(...),
):
    try:
        candidate_rows = json.loads(candidates)
        frame = await _read_frame(image)
        live_embedding = get_embedding(frame)

        best_candidate = None
        best_similarity = -1.0

        for candidate in candidate_rows:
            saved_embedding = np.array(
                json.loads(candidate["embedding"]),
                dtype=np.float32,
            )
            similarity = _cosine_similarity(saved_embedding, live_embedding)
            if similarity > best_similarity:
                best_similarity = similarity
                best_candidate = candidate

        matched = best_candidate is not None and best_similarity >= 0.72
        return {
            "match": matched,
            "success": matched,
            "similarity": float(best_similarity),
            "student_id": best_candidate.get("student_id") if matched else None,
            "message": "Student matched." if matched else "No matching student found.",
        }
    except Exception as error:
        print("ERROR:", error)
        return {
            "match": False,
            "success": False,
            "message": f"Server error: {error}",
        }


@app.post("/register-face")
async def register_face(image: UploadFile = File(...)):
    try:
        frame = await _read_frame(image)
        embedding = get_embedding(frame)

        return {
            "success": True,
            "embedding": embedding.tolist(),
            "message": "Eye lens registered successfully.",
        }
    except Exception as error:
        print("ERROR:", error)
        return {
            "success": False,
            "message": f"Server error: {error}",
        }


@app.post("/sync")
async def sync_to_server(event: dict):
    try:
        result = sync_event_to_mssql(event)
        return {"success": True, **result}
    except SyncNotConfiguredError as error:
        raise HTTPException(status_code=503, detail=str(error))
    except Exception as error:
        print("SYNC ERROR:", error)
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/login-bootstrap")
async def login_bootstrap(payload: dict):
    try:
        result = login_and_get_bundle(
            str(payload.get("role") or ""),
            str(payload.get("user_id") or ""),
            str(payload.get("password") or ""),
        )
        if result is None:
            raise HTTPException(status_code=401, detail="Invalid user ID or password.")
        return {"success": True, **result}
    except HTTPException:
        raise
    except SyncNotConfiguredError as error:
        raise HTTPException(status_code=503, detail=str(error))
    except Exception as error:
        print("LOGIN BOOTSTRAP ERROR:", error)
        raise HTTPException(status_code=500, detail=str(error))


async def _read_frame(image: UploadFile):
    data = await image.read()
    frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Invalid image frame.")
    return frame


def _cosine_similarity(emb1, emb2):
    emb1 = np.array(emb1, dtype=np.float32)
    emb2 = np.array(emb2, dtype=np.float32)
    if emb1.size == 0 or emb2.size == 0:
        return -1.0
    if emb1.shape != emb2.shape:
        size = min(emb1.size, emb2.size)
        if size < 1024:
            return -1.0
        emb1 = emb1[:size]
        emb2 = emb2[:size]

    norm1 = np.linalg.norm(emb1)
    norm2 = np.linalg.norm(emb2)
    if norm1 == 0 or norm2 == 0:
        return -1.0

    return float(np.dot(emb1 / norm1, emb2 / norm2))


if __name__ == "__main__":
     import os
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
