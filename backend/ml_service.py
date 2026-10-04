# ============================================================
# ML SERVICE
# Classical Indian Dance Mudra & Posture Recognition
# ============================================================

import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import json
from pathlib import Path

import cv2
import joblib
import mediapipe as mp
import numpy as np

from pose_evaluator import PoseEvaluator


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_DIR = Path(r"D:\Dance System")

MODEL_DIR = PROJECT_DIR / "trained_model"

BEST_MODEL_FILE = MODEL_DIR / "best_model.pkl"

LABEL_ENCODER_FILE = MODEL_DIR / "label_encoder.pkl"

BEST_MODEL_INFO_FILE = MODEL_DIR / "best_model_info.json"

REFERENCE_ANGLES_FILE = MODEL_DIR / "reference_angles.json"


# ============================================================
# FEATURE CONFIGURATION
# ============================================================

HAND_FEATURE_COUNT = 85

POSE_FEATURE_COUNT = 128

DETECTION_FLAG_COUNT = 4

EXPECTED_TOTAL_FEATURES = 302


# ============================================================
# MEDIAPIPE
# ============================================================

mp_holistic = mp.solutions.holistic


# ============================================================
# HAND FEATURE DEFINITIONS
# ============================================================

HAND_ANGLE_TRIPLETS = [

    (0, 1, 2),
    (1, 2, 3),
    (2, 3, 4),

    (0, 5, 6),
    (5, 6, 7),
    (6, 7, 8),

    (0, 9, 10),
    (9, 10, 11),
    (10, 11, 12),

    (0, 13, 14),
]


HAND_DISTANCE_PAIRS = [

    (0, 4),
    (0, 8),
    (0, 12),
    (0, 16),
    (0, 20),

    (4, 8),
    (8, 12),
    (12, 16),
    (16, 20),

    (5, 9),
    (9, 13),
    (13, 17),
]


# ============================================================
# BODY POSE FEATURE DEFINITIONS
# ============================================================

POSE_ANGLE_TRIPLETS = [

    (11, 13, 15),
    (12, 14, 16),

    (13, 11, 23),
    (14, 12, 24),

    (11, 23, 25),
    (12, 24, 26),

    (23, 25, 27),
    (24, 26, 28),

    (11, 23, 24),
    (12, 24, 23),

    (25, 23, 24),
    (26, 24, 23),
]


POSE_DISTANCE_PAIRS = [

    (11, 12),
    (23, 24),

    (11, 23),
    (12, 24),

    (11, 24),
    (12, 23),

    (13, 14),
    (15, 16),

    (25, 26),

    (23, 25),
    (24, 26),

    (25, 27),
    (26, 28),

    (27, 29),
    (28, 30),

    (29, 31),
    (30, 32),
]


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def calculate_angle(a, b, c):
    """
    Calculate angle ABC in degrees.
    """

    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)
    c = np.array(c, dtype=np.float32)

    ba = a - b
    bc = c - b

    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)

    if norm_ba < 1e-8 or norm_bc < 1e-8:
        return 0.0

    cosine = np.dot(ba, bc) / (
        norm_ba * norm_bc
    )

    cosine = np.clip(
        cosine,
        -1.0,
        1.0
    )

    return float(
        np.degrees(
            np.arccos(cosine)
        )
    )


def calculate_distance(a, b):
    """
    Calculate Euclidean distance.
    """

    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)

    return float(
        np.linalg.norm(a - b)
    )


def extract_landmark_array(
    landmark_list,
    expected_count
):
    """
    Convert MediaPipe landmarks to numpy array.
    """

    if landmark_list is None:
        return None

    if len(landmark_list.landmark) != expected_count:
        return None

    points = []

    for lm in landmark_list.landmark:

        points.append([
            lm.x,
            lm.y,
            lm.z
        ])

    return np.array(
        points,
        dtype=np.float32
    )


def normalize_landmarks(points):
    """
    Normalize landmarks around the first landmark.
    """

    if points is None:
        return None

    points = points.copy()

    origin = points[0].copy()

    points = points - origin

    scale = np.max(
        np.linalg.norm(
            points[:, :2],
            axis=1
        )
    )

    if scale > 1e-8:
        points = points / scale

    return points


def get_angle_features(
    points,
    triplets
):
    """
    Calculate angle features.
    """

    if points is None:

        return [
            0.0
            for _ in triplets
        ]

    values = []

    for a, b, c in triplets:

        values.append(
            calculate_angle(
                points[a],
                points[b],
                points[c]
            )
        )

    return values


def get_distance_features(
    points,
    pairs
):
    """
    Calculate normalized distance features.
    """

    if points is None:

        return [
            0.0
            for _ in pairs
        ]

    values = []

    for a, b in pairs:

        values.append(
            calculate_distance(
                points[a],
                points[b]
            )
        )

    return values


# ============================================================
# HAND FEATURES
# ============================================================

def create_hand_features(
    hand_landmarks
):
    """
    21 landmarks x 3 = 63
    10 angles          = 10
    12 distances       = 12

    Total = 85
    """

    if hand_landmarks is None:

        return np.zeros(
            HAND_FEATURE_COUNT,
            dtype=np.float32
        )

    points = extract_landmark_array(
        hand_landmarks,
        21
    )

    if points is None:

        return np.zeros(
            HAND_FEATURE_COUNT,
            dtype=np.float32
        )

    points = normalize_landmarks(
        points
    )

    coordinates = (
        points.flatten().tolist()
    )

    angles = get_angle_features(
        points,
        HAND_ANGLE_TRIPLETS
    )

    distances = get_distance_features(
        points,
        HAND_DISTANCE_PAIRS
    )

    features = np.array(
        coordinates
        + angles
        + distances,
        dtype=np.float32
    )

    if len(features) != HAND_FEATURE_COUNT:

        raise ValueError(
            f"Hand feature error: "
            f"expected {HAND_FEATURE_COUNT}, "
            f"got {len(features)}"
        )

    return features


# ============================================================
# POSE FEATURES
# ============================================================

def create_pose_features(
    pose_landmarks
):
    """
    33 landmarks x 3 = 99
    12 angles          = 12
    17 distances       = 17

    Total = 128
    """

    if pose_landmarks is None:

        return np.zeros(
            POSE_FEATURE_COUNT,
            dtype=np.float32
        )

    points = extract_landmark_array(
        pose_landmarks,
        33
    )

    if points is None:

        return np.zeros(
            POSE_FEATURE_COUNT,
            dtype=np.float32
        )

    points = normalize_landmarks(
        points
    )

    coordinates = (
        points.flatten().tolist()
    )

    angles = get_angle_features(
        points,
        POSE_ANGLE_TRIPLETS
    )

    distances = get_distance_features(
        points,
        POSE_DISTANCE_PAIRS
    )

    features = np.array(
        coordinates
        + angles
        + distances,
        dtype=np.float32
    )

    if len(features) != POSE_FEATURE_COUNT:

        raise ValueError(
            f"Pose feature error: "
            f"expected {POSE_FEATURE_COUNT}, "
            f"got {len(features)}"
        )

    return features


# ============================================================
# COMPLETE FEATURE EXTRACTION
# ============================================================

def extract_features_from_rgb(
    image_rgb,
    holistic
):
    """
    Extract exactly 302 features.
    """

    results = holistic.process(
        image_rgb
    )

    left_features = create_hand_features(
        results.left_hand_landmarks
    )

    right_features = create_hand_features(
        results.right_hand_landmarks
    )

    pose_features = create_pose_features(
        results.pose_landmarks
    )

    left_detected = (
        results.left_hand_landmarks
        is not None
    )

    right_detected = (
        results.right_hand_landmarks
        is not None
    )

    pose_detected = (
        results.pose_landmarks
        is not None
    )

    both_hands_detected = (
        left_detected
        and right_detected
    )

    detection_flags = np.array(
        [
            float(left_detected),
            float(right_detected),
            float(pose_detected),
            float(both_hands_detected)
        ],
        dtype=np.float32
    )

    features = np.concatenate([
        left_features,
        right_features,
        pose_features,
        detection_flags
    ])

    features = features.astype(
        np.float32
    )

    if features.shape[0] != EXPECTED_TOTAL_FEATURES:

        raise ValueError(
            f"Feature count error: "
            f"expected {EXPECTED_TOTAL_FEATURES}, "
            f"got {features.shape[0]}"
        )

    return features, results


# ============================================================
# MODEL SERVICE
# ============================================================

class DanceModelService:

    def __init__(self):

        print("\nLoading dance AI model...")

        # ----------------------------------------------------
        # CHECK MODEL FILES
        # ----------------------------------------------------

        if not BEST_MODEL_FILE.exists():

            raise FileNotFoundError(
                f"Model not found:\n"
                f"{BEST_MODEL_FILE}"
            )

        if not LABEL_ENCODER_FILE.exists():

            raise FileNotFoundError(
                f"Label encoder not found:\n"
                f"{LABEL_ENCODER_FILE}"
            )

        # ----------------------------------------------------
        # LOAD MODEL
        # ----------------------------------------------------

        self.model = joblib.load(
            BEST_MODEL_FILE
        )

        self.label_encoder = joblib.load(
            LABEL_ENCODER_FILE
        )

        # ----------------------------------------------------
        # MODEL INFORMATION
        # ----------------------------------------------------

        self.model_info = {}

        if BEST_MODEL_INFO_FILE.exists():

            with open(
                BEST_MODEL_INFO_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                self.model_info = json.load(
                    file
                )

        # ----------------------------------------------------
        # REFERENCE ANGLES
        # ----------------------------------------------------

        self.reference_angles = {}

        if REFERENCE_ANGLES_FILE.exists():

            with open(
                REFERENCE_ANGLES_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                self.reference_angles = json.load(
                    file
                )

        # ----------------------------------------------------
        # NEW POSE EVALUATOR
        # ----------------------------------------------------

        print(
            "Loading pose evaluator..."
        )

        self.pose_evaluator = (
            PoseEvaluator()
        )

        print(
            "Pose evaluator loaded successfully."
        )

        # ----------------------------------------------------
        # MEDIAPIPE HOLISTIC
        # ----------------------------------------------------

        self.holistic = (
            mp_holistic.Holistic(

                static_image_mode=True,

                model_complexity=1,

                enable_segmentation=False,

                refine_face_landmarks=False,

                min_detection_confidence=0.5,

                min_tracking_confidence=0.5
            )
        )

        # ----------------------------------------------------
        # STARTUP INFORMATION
        # ----------------------------------------------------

        print(
            "Model loaded successfully."
        )

        print(
            f"Classes: "
            f"{len(self.label_encoder.classes_)}"
        )

        print(
            f"Features: "
            f"{self.get_model_feature_count()}"
        )

        print(
            "AI model is ready."
        )

    # ========================================================
    # MODEL FEATURE COUNT
    # ========================================================

    def get_model_feature_count(self):

        if hasattr(
            self.model,
            "n_features_in_"
        ):

            return int(
                self.model.n_features_in_
            )

        if hasattr(
            self.model,
            "named_steps"
        ):

            final_model = (
                self.model.named_steps.get(
                    "model"
                )
            )

            if (
                final_model is not None
                and hasattr(
                    final_model,
                    "n_features_in_"
                )
            ):

                return int(
                    final_model.n_features_in_
                )

        return EXPECTED_TOTAL_FEATURES

    # ========================================================
    # PREDICTION
    # ========================================================

    def predict_image(
        self,
        image
    ):

        if image is None:

            raise ValueError(
                "Invalid image."
            )

        # ----------------------------------------------------
        # BGR -> RGB
        # ----------------------------------------------------

        image_rgb = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB
        )

        # ----------------------------------------------------
        # EXTRACT FEATURES
        # ----------------------------------------------------

        (
            features,
            results
        ) = extract_features_from_rgb(
            image_rgb,
            self.holistic
        )

        # ----------------------------------------------------
        # DETECTION FLAGS
        # ----------------------------------------------------

        left_hand_detected = (
            results.left_hand_landmarks
            is not None
        )

        right_hand_detected = (
            results.right_hand_landmarks
            is not None
        )

        body_detected = (
            results.pose_landmarks
            is not None
        )

        hands_detected = (
            left_hand_detected
            or right_hand_detected
        )

        person_detected = (
            body_detected
            and hands_detected
        )

        # ====================================================
        # WAITING STATE
        # ====================================================

        if not person_detected:

            if not body_detected:

                message = (
                    "Waiting for pose. "
                    "Please move into the camera frame "
                    "and keep your full body visible."
                )

            elif not hands_detected:

                message = (
                    "Body detected. "
                    "Please bring at least one hand "
                    "clearly into the camera view."
                )

            else:

                message = (
                    "Waiting for a clear dance pose."
                )

            return {

                "status": "waiting",

                "message": message,

                "prediction": None,

                "confidence": 0.0,

                "pose_similarity": 0.0,

                "left_hand_detected": (
                    left_hand_detected
                ),

                "right_hand_detected": (
                    right_hand_detected
                ),

                "body_detected": (
                    body_detected
                ),

                "top_predictions": [],

                "feedback": [],

                "improvement_feedback": ""
            }

        # ====================================================
        # CHECK FEATURE COUNT
        # ====================================================

        expected_features = (
            self.get_model_feature_count()
        )

        if (
            features.shape[0]
            != expected_features
        ):

            raise ValueError(
                f"Model expects "
                f"{expected_features} features, "
                f"but live input contains "
                f"{features.shape[0]}."
            )

        # ====================================================
        # PREPARE INPUT
        # ====================================================

        x = features.reshape(
            1,
            -1
        )

        # ====================================================
        # MODEL PREDICTION
        # ====================================================

        try:

            probabilities = (
                self.model.predict_proba(
                    x
                )[0]
            )

            probabilities = np.asarray(
                probabilities,
                dtype=np.float32
            )

        except Exception:

            predicted_index = int(
                self.model.predict(x)[0]
            )

            probabilities = np.zeros(
                len(
                    self.label_encoder.classes_
                ),
                dtype=np.float32
            )

            probabilities[
                predicted_index
            ] = 1.0

        # ====================================================
        # GET PREDICTED CLASS
        # ====================================================

        predicted_index = int(
            np.argmax(
                probabilities
            )
        )

        prediction = (
            self.label_encoder
            .inverse_transform(
                [predicted_index]
            )[0]
        )

        confidence = float(
            probabilities[
                predicted_index
            ] * 100.0
        )

        # ====================================================
        # TOP 3 PREDICTIONS
        # ====================================================

        order = np.argsort(
            probabilities
        )[::-1]

        top_predictions = []

        for index in order[:3]:

            class_name = (
                self.label_encoder
                .inverse_transform(
                    [int(index)]
                )[0]
            )

            top_predictions.append({

                "label": class_name,

                "confidence": round(
                    float(
                        probabilities[index]
                        * 100.0
                    ),
                    2
                )
            })

        # ====================================================
        # NEW DETAILED POSE EVALUATION
        # ====================================================

        evaluation = (
            self.pose_evaluator.evaluate_pose(

                features=features,

                prediction=prediction,

                left_hand_detected=(
                    left_hand_detected
                ),

                right_hand_detected=(
                    right_hand_detected
                ),

                body_detected=(
                    body_detected
                )
            )
        )

        # ----------------------------------------------------
        # GET EVALUATION SIMILARITY
        # ----------------------------------------------------

        pose_similarity = float(
            evaluation.get(
                "similarity",
                0.0
            )
        )

        # ----------------------------------------------------
        # GET FEEDBACK
        # ----------------------------------------------------

        feedback = evaluation.get(
            "feedback",
            []
        )

        if not isinstance(
            feedback,
            list
        ):

            feedback = [
                str(feedback)
            ]

        # ----------------------------------------------------
        # CREATE SINGLE FEEDBACK STRING
        # ----------------------------------------------------

        improvement_feedback = " ".join(
            str(item)
            for item in feedback
        )

        # ====================================================
        # FINAL RESULT
        # ====================================================

        return {

            "status": "recognized",

            "message": "Pose detected.",

            "prediction": prediction,

            "confidence": round(
                confidence,
                2
            ),

            "pose_similarity": round(
                pose_similarity,
                2
            ),

            "left_hand_detected": (
                left_hand_detected
            ),

            "right_hand_detected": (
                right_hand_detected
            ),

            "body_detected": (
                body_detected
            ),

            "top_predictions": (
                top_predictions
            ),

            # ----------------------------------------------
            # NEW EVALUATION DATA
            # ----------------------------------------------

            "feedback": feedback,

            "improvement_feedback": (
                improvement_feedback
            ),

            "evaluation_details": (
                evaluation.get(
                    "details",
                    {}
                )
            )
        }

    # ========================================================
    # OLD ANGLE COMPARISON
    # ========================================================

    def compare_angles(
        self,
        live_features,
        reference
    ):
        """
        Kept for compatibility with the existing backend.

        The new PoseEvaluator is now used for detailed
        evaluation inside predict_image().
        """

        live_left = (
            live_features[63:73]
        )

        live_right = (
            live_features[148:158]
        )

        live_pose = (
            live_features[269:281]
        )

        ref_left = np.array(
            reference[
                "left_hand_angles"
            ],
            dtype=np.float32
        )

        ref_right = np.array(
            reference[
                "right_hand_angles"
            ],
            dtype=np.float32
        )

        ref_pose = np.array(
            reference[
                "pose_angles"
            ],
            dtype=np.float32
        )

        left_difference = np.abs(
            live_left - ref_left
        )

        right_difference = np.abs(
            live_right - ref_right
        )

        pose_difference = np.abs(
            live_pose - ref_pose
        )

        all_differences = np.concatenate([
            left_difference,
            right_difference,
            pose_difference
        ])

        if all_differences.size == 0:

            return 0.0

        overall_difference = float(
            np.mean(
                all_differences
            )
        )

        similarity = (
            100.0
            * (
                1.0
                - min(
                    overall_difference / 180.0,
                    1.0
                )
            )
        )

        return max(
            0.0,
            min(
                100.0,
                similarity
            )
        )

    # ========================================================
    # MODEL INFORMATION
    # ========================================================

    def get_model_info(self):

        return {

            "model": self.model_info.get(
                "best_model",
                "Unknown"
            ),

            "feature_count": (
                self.model_info.get(
                    "feature_count",
                    EXPECTED_TOTAL_FEATURES
                )
            ),

            "class_count": (
                self.model_info.get(
                    "class_count",
                    len(
                        self.label_encoder.classes_
                    )
                )
            ),

            "classes": (
                self.label_encoder
                .classes_
                .tolist()
            ),

            "dataset_size": (
                self.model_info.get(
                    "dataset_size"
                )
            ),

            "macro_f1": (
                self.model_info.get(
                    "best_macro_f1"
                )
            )
        }

    # ========================================================
    # CLEANUP
    # ========================================================

    def close(self):

        if self.holistic:

            self.holistic.close()