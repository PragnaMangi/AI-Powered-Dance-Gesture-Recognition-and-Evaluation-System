# ============================================================
# FASTAPI BACKEND
# Classical Indian Dance AI System
# ============================================================

from contextlib import asynccontextmanager
from datetime import datetime, timezone

import os
import cv2
import numpy as np

from dotenv import load_dotenv

load_dotenv()

from fastapi import (
    FastAPI,
    File,
    UploadFile,
    HTTPException
)

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from pymongo import MongoClient

from ml_service import DanceModelService


# ============================================================
# GLOBAL MODEL
# ============================================================

dance_model = None


# ============================================================
# MONGODB
# ============================================================

mongo_client = None
mongo_db = None
sessions_collection = None


# ============================================================
# MONGODB CONNECTION
# ============================================================

def connect_mongodb():

    global mongo_client
    global mongo_db
    global sessions_collection

    mongo_uri = os.getenv("MONGODB_URI")

    if not mongo_uri:
        print("\nWARNING: MONGODB_URI is not set.")
        print("Session history will not be available.")
        return

    try:

        print("\nConnecting to MongoDB Atlas...")

        mongo_client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000
        )

        # Test connection
        mongo_client.admin.command("ping")

        # Use database from environment if available.
        # Otherwise use KuchipudiAI.
        database_name = os.getenv(
            "MONGODB_DATABASE",
            "KuchipudiAI"
        )

        mongo_db = mongo_client[database_name]

        sessions_collection = mongo_db["practice_sessions"]

        print("MongoDB Atlas connected successfully.")
        print(
            f"Database: {database_name}"
        )
        print(
            "Collection: practice_sessions"
        )

    except Exception as error:

        print(
            "\nWARNING: MongoDB connection failed:"
        )

        print(error)

        mongo_client = None
        mongo_db = None
        sessions_collection = None


# ============================================================
# APPLICATION STARTUP / SHUTDOWN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    global dance_model

    print("\n" + "=" * 60)
    print("STARTING CLASSICAL DANCE AI BACKEND")
    print("=" * 60)

    # --------------------------------------------------------
    # MongoDB
    # --------------------------------------------------------

    connect_mongodb()

    # --------------------------------------------------------
    # AI MODEL
    # --------------------------------------------------------

    try:

        dance_model = DanceModelService()

        print("\nAI model is ready.")

    except Exception as error:

        print(
            "\nERROR loading AI model:"
        )

        print(error)

        raise

    yield

    # --------------------------------------------------------
    # SHUTDOWN
    # --------------------------------------------------------

    print(
        "\nShutting down AI model..."
    )

    if dance_model is not None:

        dance_model.close()

    if mongo_client is not None:

        mongo_client.close()

        print(
            "MongoDB connection closed."
        )


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(

    title="Classical Dance AI API",

    description=(
        "AI-powered Classical Indian Dance "
        "Mudra and Posture Recognition API"
    ),

    version="1.0.0",

    lifespan=lifespan
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {

        "message": (
            "Classical Dance AI Backend "
            "is running."
        ),

        "status": "online"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    if dance_model is None:

        return {

            "status": "starting",

            "model_loaded": False
        }

    return {

        "status": "healthy",

        "model_loaded": True,

        "mongodb_connected": (
            sessions_collection is not None
        )
    }


# ============================================================
# MODEL INFORMATION
# ============================================================

@app.get("/model-info")
def model_info():

    if dance_model is None:

        raise HTTPException(
            status_code=503,
            detail="AI model is not loaded."
        )

    return dance_model.get_model_info()


# ============================================================
# RECOGNIZE IMAGE
# ============================================================

@app.post("/predict")
async def predict(
    file: UploadFile = File(...)
):

    if dance_model is None:

        raise HTTPException(
            status_code=503,
            detail="AI model is not loaded."
        )

    # --------------------------------------------------------
    # Validate file type
    # --------------------------------------------------------

    allowed_types = {

        "image/jpeg",
        "image/png",
        "image/jpg",
        "image/webp"
    }

    if file.content_type not in allowed_types:

        raise HTTPException(

            status_code=400,

            detail=(
                "Please upload a valid image "
                "(JPG, JPEG, PNG or WEBP)."
            )
        )

    # --------------------------------------------------------
    # Read image
    # --------------------------------------------------------

    try:

        image_bytes = await file.read()

        if not image_bytes:

            raise ValueError(
                "Empty image file."
            )

        image_array = np.frombuffer(
            image_bytes,
            dtype=np.uint8
        )

        image = cv2.imdecode(
            image_array,
            cv2.IMREAD_COLOR
        )

        if image is None:

            raise ValueError(
                "Could not decode image."
            )

    except Exception as error:

        raise HTTPException(

            status_code=400,

            detail=f"Invalid image: {error}"
        )

    # --------------------------------------------------------
    # AI prediction
    # --------------------------------------------------------

    try:

        result = (
            dance_model.predict_image(
                image
            )
        )

        return result

    except Exception as error:

        print(
            "\nPrediction error:"
        )

        print(error)

        raise HTTPException(

            status_code=500,

            detail=(
                "Prediction failed. "
                "Please try again."
            )
        )


# ============================================================
# AVAILABLE CLASSES
# ============================================================

@app.get("/classes")
def classes():

    if dance_model is None:

        raise HTTPException(
            status_code=503,
            detail="AI model is not loaded."
        )

    return {

        "classes": (
            dance_model
            .label_encoder
            .classes_
            .tolist()
        )
    }


# ============================================================
# PRACTICE SESSION MODEL
# ============================================================

class PracticeSession(BaseModel):

    pose: str

    confidence: float

    score: float

    status: str = "Practice"


# ============================================================
# SAVE PRACTICE SESSION
# ============================================================

@app.post("/sessions")
def save_session(
    session: PracticeSession
):

    if sessions_collection is None:

        raise HTTPException(

            status_code=503,

            detail=(
                "MongoDB is not connected. "
                "Practice session cannot be saved."
            )
        )

    try:

        # ----------------------------------------------------
        # Determine status automatically
        # ----------------------------------------------------

        if session.score >= 90:

            status = "Excellent"

        elif session.score >= 80:

            status = "Good"

        else:

            status = "Practice"

        # ----------------------------------------------------
        # Create session document
        # ----------------------------------------------------

        session_document = {

            "pose": session.pose,

            "confidence": round(
                float(session.confidence),
                2
            ),

            "score": round(
                float(session.score),
                2
            ),

            "status": status,

            "created_at": datetime.now(
                timezone.utc
            )
        }

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        insert_result = (
            sessions_collection.insert_one(
                session_document
            )
        )

        print(
            "\nPractice session saved:"
        )

        print(
            session_document
        )

        return {

            "success": True,

            "message": (
                "Practice session saved successfully."
            ),

            "session_id": str(
                insert_result.inserted_id
            )
        }

    except Exception as error:

        print(
            "\nSession save error:"
        )

        print(error)

        raise HTTPException(

            status_code=500,

            detail=(
                "Could not save practice session."
            )
        )


# ============================================================
# GET PRACTICE SESSIONS
# ============================================================

@app.get("/sessions")
def get_sessions():

    if sessions_collection is None:

        raise HTTPException(

            status_code=503,

            detail=(
                "MongoDB is not connected."
            )
        )

    try:

        documents = list(
            sessions_collection
            .find({})
            .sort(
                "created_at",
                -1
            )
        )

        sessions = []

        for document in documents:

            created_at = (
                document.get(
                    "created_at"
                )
            )

            # Convert MongoDB datetime
            # to ISO string for React.
            if created_at:

                created_at_string = (
                    created_at.isoformat()
                )

            else:

                created_at_string = ""

            sessions.append({

                "id": str(
                    document.get("_id")
                ),

                "pose": document.get(
                    "pose",
                    "Unknown"
                ),

                "confidence": float(
                    document.get(
                        "confidence",
                        0
                    )
                ),

                "score": float(
                    document.get(
                        "score",
                        0
                    )
                ),

                "status": document.get(
                    "status",
                    "Practice"
                ),

                "created_at":
                    created_at_string

            })

        return {

            "success": True,

            "count": len(sessions),

            "sessions": sessions
        }

    except Exception as error:

        print(
            "\nSession retrieval error:"
        )

        print(error)

        raise HTTPException(

            status_code=500,

            detail=(
                "Could not retrieve practice sessions."
            )
        )


# ============================================================
# DELETE ALL PRACTICE SESSIONS
# ============================================================

@app.delete("/sessions")
def delete_sessions():

    if sessions_collection is None:

        raise HTTPException(

            status_code=503,

            detail=(
                "MongoDB is not connected."
            )
        )

    try:

        result = (
            sessions_collection
            .delete_many({})
        )

        return {

            "success": True,

            "deleted_count":
                result.deleted_count,

            "message":
                "Practice history cleared."
        }

    except Exception as error:

        print(
            "\nSession deletion error:"
        )

        print(error)

        raise HTTPException(

            status_code=500,

            detail=(
                "Could not clear practice history."
            )
        )


# ============================================================
# START MESSAGE
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(

        "main:app",

        host="127.0.0.1",

        port=8000,

        reload=True
    )