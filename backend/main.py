
# ============================================================
# FASTAPI BACKEND
# Classical Indian Dance AI System
# Multi-User Authentication + AI Recognition
# ============================================================

from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta

import os
import cv2
import numpy as np

from dotenv import load_dotenv

load_dotenv()

from fastapi import (
    FastAPI,
    File,
    UploadFile,
    HTTPException,
    Depends
)

from fastapi.middleware.cors import CORSMiddleware

from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm
)

from pydantic import BaseModel

from pymongo import MongoClient
from bson import ObjectId

from jose import jwt, JWTError

from passlib.context import CryptContext

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
users_collection = None


# ============================================================
# AUTHENTICATION SETTINGS
# ============================================================

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "kuchipudi-ai-development-secret-change-this"
)

JWT_ALGORITHM = "HS256"

JWT_EXPIRE_MINUTES = 60 * 24


# ============================================================
# PASSWORD HASHING
# ============================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# ============================================================
# OAUTH2
# ============================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


# ============================================================
# MONGODB CONNECTION
# ============================================================

def connect_mongodb():

    global mongo_client
    global mongo_db
    global sessions_collection
    global users_collection

    mongo_uri = os.getenv("MONGODB_URI")

    if not mongo_uri:

        print("\nWARNING: MONGODB_URI is not set.")

        print(
            "MongoDB features will not be available."
        )

        return

    try:

        print(
            "\nConnecting to MongoDB Atlas..."
        )

        mongo_client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000
        )

        # Test connection
        mongo_client.admin.command("ping")

        database_name = os.getenv(
            "MONGODB_DATABASE",
            "KuchipudiAI"
        )

        mongo_db = mongo_client[
            database_name
        ]

        sessions_collection = mongo_db[
            "practice_sessions"
        ]

        users_collection = mongo_db[
            "users"
        ]

        # ----------------------------------------------------
        # Unique email index
        # ----------------------------------------------------

        users_collection.create_index(
            "email",
            unique=True
        )

        print(
            "MongoDB Atlas connected successfully."
        )

        print(
            f"Database: {database_name}"
        )

        print(
            "Collections:"
        )

        print(
            "  - users"
        )

        print(
            "  - practice_sessions"
        )

    except Exception as error:

        print(
            "\nWARNING: MongoDB connection failed:"
        )

        print(error)

        mongo_client = None
        mongo_db = None
        sessions_collection = None
        users_collection = None


# ============================================================
# APPLICATION STARTUP / SHUTDOWN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    global dance_model

    print("\n" + "=" * 60)

    print(
        "STARTING CLASSICAL DANCE AI BACKEND"
    )

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

        print(
            "\nAI model is ready."
        )

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
        "Mudra and Posture Recognition API "
        "with multi-user authentication."
    ),

    version="2.0.0",

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

        "status": "online",

        "authentication": "enabled"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    if dance_model is None:

        return {

            "status": "starting",

            "model_loaded": False,

            "mongodb_connected": (
                sessions_collection is not None
            ),

            "users_collection": (
                users_collection is not None
            )
        }

    return {

        "status": "healthy",

        "model_loaded": True,

        "mongodb_connected": (
            sessions_collection is not None
        ),

        "users_collection": (
            users_collection is not None
        )
    }


# ============================================================
# PASSWORD HELPERS
# ============================================================

def hash_password(password: str):

    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
):

    return pwd_context.verify(
        plain_password,
        hashed_password
    )


# ============================================================
# JWT HELPERS
# ============================================================

def create_access_token(
    user_id: str
):

    expire = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=JWT_EXPIRE_MINUTES
        )
    )

    payload = {

        "sub": user_id,

        "exp": expire
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )


# ============================================================
# GET CURRENT USER
# ============================================================

def get_current_user(
    token: str = Depends(oauth2_scheme)
):

    if users_collection is None:

        raise HTTPException(

            status_code=503,

            detail=(
                "MongoDB is not connected."
            )
        )

    credentials_exception = HTTPException(

        status_code=401,

        detail="Invalid or expired authentication token.",

        headers={
            "WWW-Authenticate": "Bearer"
        }
    )

    try:

        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

        user_id = payload.get("sub")

        if not user_id:

            raise credentials_exception

    except JWTError:

        raise credentials_exception

    try:

        user = users_collection.find_one(
            {
                "_id": ObjectId(user_id)
            }
        )

    except Exception:

        raise credentials_exception

    if user is None:

        raise credentials_exception

    return user


# ============================================================
# AUTH MODELS
# ============================================================

class SignupRequest(BaseModel):

    name: str

    email: str

    password: str


class ProfileUpdate(BaseModel):

    name: str

    bio: str = ""


# ============================================================
# SIGN UP
# ============================================================

@app.post("/auth/signup")
def signup(
    request: SignupRequest
):

    if users_collection is None:

        raise HTTPException(

            status_code=503,

            detail=(
                "MongoDB is not connected."
            )
        )

    # --------------------------------------------------------
    # Clean input
    # --------------------------------------------------------

    name = request.name.strip()

    email = request.email.strip().lower()

    password = request.password

    # --------------------------------------------------------
    # Validate name
    # --------------------------------------------------------

    if len(name) < 2:

        raise HTTPException(

            status_code=400,

            detail=(
                "Name must contain at least "
                "2 characters."
            )
        )

    # --------------------------------------------------------
    # Validate email
    # --------------------------------------------------------

    if "@" not in email or "." not in email:

        raise HTTPException(

            status_code=400,

            detail="Please enter a valid email address."
        )

    # --------------------------------------------------------
    # Validate password
    # --------------------------------------------------------

    if len(password) < 6:

        raise HTTPException(

            status_code=400,

            detail=(
                "Password must contain at least "
                "6 characters."
            )
        )

    # --------------------------------------------------------
    # Check existing user
    # --------------------------------------------------------

    existing_user = users_collection.find_one(
        {
            "email": email
        }
    )

    if existing_user:

        raise HTTPException(

            status_code=409,

            detail=(
                "An account with this email "
                "already exists."
            )
        )

    # --------------------------------------------------------
    # Create user
    # --------------------------------------------------------

    password_hash = hash_password(
        password
    )

    user_document = {

        "name": name,

        "email": email,

        "password_hash": password_hash,

        "bio": "",

        "created_at": datetime.now(
            timezone.utc
        )
    }

    try:

        insert_result = (
            users_collection.insert_one(
                user_document
            )
        )

        user_id = str(
            insert_result.inserted_id
        )

        token = create_access_token(
            user_id
        )

        return {

            "success": True,

            "message": (
                "Account created successfully."
            ),

            "access_token": token,

            "token": token,

            "token_type": "bearer",

            "user": {

                "id": user_id,

                "name": name,

                "email": email,

                "bio": ""
            }
        }

    except Exception as error:

        print(
            "\nSignup error:"
        )

        print(error)

        raise HTTPException(

            status_code=500,

            detail=(
                "Could not create account."
            )
        )


# ============================================================
# LOGIN
#
# IMPORTANT:
# OAuth2PasswordRequestForm is used here so that Swagger's
# Authorize button works correctly.
#
# Swagger sends:
# username = user's email
# password = user's password
#
# Swagger expects:
# access_token
# token_type
# ============================================================

@app.post("/auth/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends()
):

    if users_collection is None:

        raise HTTPException(

            status_code=503,

            detail=(
                "MongoDB is not connected."
            )
        )

    # OAuth2 calls the field "username".
    # Our application uses email as the username.

    email = form_data.username.strip().lower()

    password = form_data.password

    # --------------------------------------------------------
    # Find user
    # --------------------------------------------------------

    user = users_collection.find_one(
        {
            "email": email
        }
    )

    if user is None:

        raise HTTPException(

            status_code=401,

            detail="Invalid email or password.",

            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    # --------------------------------------------------------
    # Verify password
    # --------------------------------------------------------

    password_valid = verify_password(

        password,

        user.get(
            "password_hash",
            ""
        )
    )

    if not password_valid:

        raise HTTPException(

            status_code=401,

            detail="Invalid email or password.",

            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    # --------------------------------------------------------
    # Create JWT token
    # --------------------------------------------------------

    token = create_access_token(

        str(user["_id"])
    )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # "access_token" is required by Swagger OAuth2.
    #
    # "token" is also returned so the React frontend
    # can use data.token if required.
    # --------------------------------------------------------

    return {

        "success": True,

        "message": "Login successful.",

        "access_token": token,

        "token": token,

        "token_type": "bearer",

        "user": {

            "id": str(
                user["_id"]
            ),

            "name": user.get(
                "name",
                ""
            ),

            "email": user.get(
                "email",
                ""
            ),

            "bio": user.get(
                "bio",
                ""
            )
        }
    }


# ============================================================
# GET CURRENT USER
# ============================================================

@app.get("/auth/me")
def get_me(
    current_user=Depends(
        get_current_user
    )
):

    return {

        "success": True,

        "user": {

            "id": str(
                current_user["_id"]
            ),

            "name": current_user.get(
                "name",
                ""
            ),

            "email": current_user.get(
                "email",
                ""
            ),

            "bio": current_user.get(
                "bio",
                ""
            )
        }
    }


# ============================================================
# UPDATE PROFILE
# ============================================================

@app.put("/profile")
def update_profile(
    profile: ProfileUpdate,

    current_user=Depends(
        get_current_user
    )
):

    if users_collection is None:

        raise HTTPException(

            status_code=503,

            detail=(
                "MongoDB is not connected."
            )
        )

    name = profile.name.strip()

    bio = profile.bio.strip()

    if len(name) < 2:

        raise HTTPException(

            status_code=400,

            detail=(
                "Name must contain at least "
                "2 characters."
            )
        )

    try:

        users_collection.update_one(

            {
                "_id": current_user["_id"]
            },

            {
                "$set": {

                    "name": name,

                    "bio": bio
                }
            }
        )

        return {

            "success": True,

            "message": (
                "Profile updated successfully."
            ),

            "user": {

                "id": str(
                    current_user["_id"]
                ),

                "name": name,

                "email": current_user.get(
                    "email",
                    ""
                ),

                "bio": bio
            }
        }

    except Exception as error:

        print(
            "\nProfile update error:"
        )

        print(error)

        raise HTTPException(

            status_code=500,

            detail=(
                "Could not update profile."
            )
        )


# ============================================================
# MODEL INFORMATION
# ============================================================

@app.get("/model-info")
def model_info():

    if dance_model is None:

        raise HTTPException(

            status_code=503,

            detail=(
                "AI model is not loaded."
            )
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

            detail=(
                "AI model is not loaded."
            )
        )

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

            detail=(
                "AI model is not loaded."
            )
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

    session: PracticeSession,

    current_user=Depends(
        get_current_user
    )

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

            "user_id": current_user["_id"],

            "pose": session.pose,

            "confidence": round(

                float(
                    session.confidence
                ),

                2
            ),

            "score": round(

                float(
                    session.score
                ),

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
# GET CURRENT USER'S PRACTICE SESSIONS
# ============================================================

@app.get("/sessions")
def get_sessions(

    current_user=Depends(
        get_current_user
    )

):

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

            .find(
                {
                    "user_id": current_user["_id"]
                }
            )

            .sort(
                "created_at",
                -1
            )
        )

        sessions = []

        for document in documents:

            created_at = document.get(
                "created_at"
            )

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
# DELETE CURRENT USER'S PRACTICE SESSIONS
# ============================================================

@app.delete("/sessions")
def delete_sessions(

    current_user=Depends(
        get_current_user
    )

):

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

            .delete_many(

                {
                    "user_id":
                        current_user["_id"]
                }
            )
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
