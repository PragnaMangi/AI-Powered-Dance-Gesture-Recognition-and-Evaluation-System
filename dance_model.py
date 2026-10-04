
# ============================================================
# IMPORTS
# ============================================================

import os

# Reduce unnecessary TensorFlow/MediaPipe console messages
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import re
import json
import cv2
import joblib
import numpy as np
import mediapipe as mp

from pathlib import Path
from collections import deque

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline

from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score
)

import matplotlib.pyplot as plt


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_DIR = Path(r"D:\Dance System")

DATASET_DIR = PROJECT_DIR / "dataset" / "ALL"

MODEL_DIR = PROJECT_DIR / "trained_model"

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# SAVED FILES
# ============================================================

FEATURES_FILE = MODEL_DIR / "features.npz"

LABELS_FILE = MODEL_DIR / "labels.npy"

IMAGE_PATHS_FILE = MODEL_DIR / "image_paths.json"

SCALER_FILE = MODEL_DIR / "scaler.pkl"

LABEL_ENCODER_FILE = MODEL_DIR / "label_encoder.pkl"

BEST_MODEL_FILE = MODEL_DIR / "best_model.pkl"

BEST_MODEL_INFO_FILE = MODEL_DIR / "best_model_info.json"

MODEL_RESULTS_FILE = MODEL_DIR / "model_results.json"

REFERENCE_ANGLES_FILE = MODEL_DIR / "reference_angles.json"

CONFUSION_MATRIX_FILE = (
    MODEL_DIR / "confusion_matrix_best_model.png"
)

CLASSIFICATION_REPORT_FILE = (
    MODEL_DIR / "classification_report.txt"
)


# ============================================================
# FEATURE COUNTS
# ============================================================

HAND_FEATURE_COUNT = 85

POSE_FEATURE_COUNT = 128

DETECTION_FLAG_COUNT = 4

TOTAL_FEATURE_COUNT = (
    HAND_FEATURE_COUNT
    + HAND_FEATURE_COUNT
    + POSE_FEATURE_COUNT
    + DETECTION_FLAG_COUNT
)

EXPECTED_TOTAL_FEATURES = 302


# Safety check
if TOTAL_FEATURE_COUNT != EXPECTED_TOTAL_FEATURES:
    raise RuntimeError(
        f"Feature configuration error. "
        f"Expected {EXPECTED_TOTAL_FEATURES}, "
        f"but calculated {TOTAL_FEATURE_COUNT}."
    )


# ============================================================
# MEDIAPIPE
# ============================================================

mp_holistic = mp.solutions.holistic

mp_drawing = mp.solutions.drawing_utils


# ============================================================
# HAND LANDMARK FEATURES
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
# BODY POSE FEATURES
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


# IMPORTANT:
# EXACTLY 17 PAIRS
#
# Do NOT add (27,31)
# Do NOT add (28,32)
#
# This keeps the pose feature count at 128
# and total feature count at 302.

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

    a = np.array(
        a,
        dtype=np.float32
    )

    b = np.array(
        b,
        dtype=np.float32
    )

    c = np.array(
        c,
        dtype=np.float32
    )

    ba = a - b

    bc = c - b

    norm_ba = np.linalg.norm(ba)

    norm_bc = np.linalg.norm(bc)

    if norm_ba < 1e-8 or norm_bc < 1e-8:
        return 0.0

    cosine = (
        np.dot(ba, bc)
        / (norm_ba * norm_bc)
    )

    cosine = np.clip(
        cosine,
        -1.0,
        1.0
    )

    angle = np.degrees(
        np.arccos(cosine)
    )

    return float(angle)


def calculate_distance(a, b):
    """
    Calculate Euclidean distance.
    """

    a = np.array(
        a,
        dtype=np.float32
    )

    b = np.array(
        b,
        dtype=np.float32
    )

    return float(
        np.linalg.norm(a - b)
    )


def extract_landmark_array(
    landmark_list,
    expected_count
):
    """
    Convert MediaPipe landmarks
    into numpy array.
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
    Normalize landmarks around
    the first landmark.

    This reduces sensitivity to
    absolute image position and scale.
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
    Calculate multiple angles.
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
    Calculate normalized distances.
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
    One hand:

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
        points
        .flatten()
        .tolist()
    )

    angles = get_angle_features(
        points,
        HAND_ANGLE_TRIPLETS
    )

    distances = get_distance_features(
        points,
        HAND_DISTANCE_PAIRS
    )

    features = (
        coordinates
        + angles
        + distances
    )

    features = np.array(
        features,
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
    Body pose:

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
        points
        .flatten()
        .tolist()
    )

    angles = get_angle_features(
        points,
        POSE_ANGLE_TRIPLETS
    )

    distances = get_distance_features(
        points,
        POSE_DISTANCE_PAIRS
    )

    features = (
        coordinates
        + angles
        + distances
    )

    features = np.array(
        features,
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

    Left hand  = 85
    Right hand = 85
    Pose       = 128
    Flags      = 4

    TOTAL = 302
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
            f"FEATURE COUNT ERROR: "
            f"Expected {EXPECTED_TOTAL_FEATURES}, "
            f"but received {features.shape[0]}."
        )

    return features, results


# ============================================================
# IMAGE FEATURE EXTRACTION
# ============================================================

def extract_features_from_image(
    image_path,
    holistic
):
    """
    Read image and extract features.
    """

    image = cv2.imread(
        str(image_path)
    )

    if image is None:

        return None

    image_rgb = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    features, _ = extract_features_from_rgb(
        image_rgb,
        holistic
    )

    return features


# ============================================================
# LABEL EXTRACTION
# ============================================================

def extract_label_from_filename(
    filename
):
    """
    Extract class label.

    Example:

        Pataka (1).jpg
        -> Pataka

        Alapadma (25).JPG
        -> Alapadma
    """

    stem = Path(
        filename
    ).stem

    match = re.match(
        r"^(.*?)\s*\(\d+\)$",
        stem
    )

    if match:

        label = match.group(1).strip()

    else:

        label = re.sub(
            r"\s*\d+$",
            "",
            stem
        ).strip()

    return label


# ============================================================
# DATASET DISCOVERY
# ============================================================

def get_dataset_images():
    """
    Find all supported image files
    recursively.
    """

    extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".JPG",
        ".JPEG",
        ".PNG",
        ".BMP"
    }

    image_paths = []

    for path in DATASET_DIR.rglob("*"):

        if (
            path.is_file()
            and path.suffix in extensions
        ):

            image_paths.append(path)

    image_paths.sort()

    return image_paths


# ============================================================
# DATASET FEATURE EXTRACTION
# ============================================================

def build_dataset():
    """
    Extract MediaPipe features
    from every image.
    """

    print("\n" + "=" * 70)
    print("DATASET FEATURE EXTRACTION")
    print("=" * 70)

    print(
        f"\nDataset folder:\n"
        f"{DATASET_DIR}"
    )

    if not DATASET_DIR.exists():

        print(
            "\nERROR: Dataset folder "
            "does not exist."
        )

        return None, None, None

    image_paths = get_dataset_images()

    print(
        f"\nTotal images found: "
        f"{len(image_paths)}"
    )

    if len(image_paths) == 0:

        print(
            "ERROR: No images found."
        )

        return None, None, None

    X = []

    y = []

    valid_paths = []

    failed_images = []

    print(
        "\nStarting MediaPipe "
        "feature extraction...\n"
    )

    with mp_holistic.Holistic(
        static_image_mode=True,
        model_complexity=1,
        enable_segmentation=False,
        refine_face_landmarks=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as holistic:

        for index, image_path in enumerate(
            image_paths,
            start=1
        ):

            try:

                features = (
                    extract_features_from_image(
                        image_path,
                        holistic
                    )
                )

                if features is None:

                    failed_images.append(
                        str(image_path)
                    )

                    continue

                if len(features) != EXPECTED_TOTAL_FEATURES:

                    failed_images.append(
                        f"{image_path} | "
                        f"Wrong feature count"
                    )

                    continue

                label = (
                    extract_label_from_filename(
                        image_path.name
                    )
                )

                X.append(features)

                y.append(label)

                valid_paths.append(
                    str(image_path)
                )

                if (
                    index % 25 == 0
                    or index == len(image_paths)
                ):

                    print(
                        f"Processed: "
                        f"{index}/"
                        f"{len(image_paths)}"
                    )

            except Exception as error:

                failed_images.append(
                    f"{image_path} | {error}"
                )

    X = np.array(
        X,
        dtype=np.float32
    )

    y = np.array(
        y
    )

    print(
        "\n" + "-" * 70
    )

    print(
        "FEATURE EXTRACTION COMPLETE"
    )

    print(
        "-" * 70
    )

    print(
        f"Valid images: "
        f"{len(X)}"
    )

    print(
        f"Failed images: "
        f"{len(failed_images)}"
    )

    if len(X) == 0:

        print(
            "\nERROR: No valid "
            "features were extracted."
        )

        return None, None, None

    print(
        f"Feature shape: "
        f"{X.shape}"
    )

    print(
        f"Features per image: "
        f"{X.shape[1]}"
    )

    if X.shape[1] != EXPECTED_TOTAL_FEATURES:

        raise ValueError(
            f"Dataset feature matrix "
            f"must have {EXPECTED_TOTAL_FEATURES} "
            f"features, but has "
            f"{X.shape[1]}."
        )

    classes, counts = np.unique(
        y,
        return_counts=True
    )

    print(
        "\nClasses:"
    )

    for class_name, count in zip(
        classes,
        counts
    ):

        print(
            f"  {class_name:<20} "
            f"{count}"
        )

    # --------------------------------------------------------
    # SAVE FEATURES
    # --------------------------------------------------------

    np.savez_compressed(
        FEATURES_FILE,
        X=X
    )

    np.save(
        LABELS_FILE,
        y
    )

    with open(
        IMAGE_PATHS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            valid_paths,
            file,
            indent=2
        )

    failed_file = (
        MODEL_DIR / "failed_images.csv"
    )

    with open(
        failed_file,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "image_path\n"
        )

        for item in failed_images:

            file.write(
                str(item)
                .replace("\n", " ")
                + "\n"
            )

    print(
        f"\nSaved features to:\n"
        f"{FEATURES_FILE}"
    )

    return X, y, valid_paths


# ============================================================
# LOAD EXISTING DATASET
# ============================================================

def load_existing_dataset():
    """
    Load previously extracted features.
    """

    if (
        FEATURES_FILE.exists()
        and LABELS_FILE.exists()
        and IMAGE_PATHS_FILE.exists()
    ):

        print(
            "\nExisting extracted "
            "features found."
        )

        use_existing = input(
            "\nUse existing extracted "
            "features? (Y/N): "
        ).strip().lower()

        if use_existing == "y":

            data = np.load(
                FEATURES_FILE
            )

            X = data["X"]

            y = np.load(
                LABELS_FILE,
                allow_pickle=True
            )

            with open(
                IMAGE_PATHS_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                paths = json.load(
                    file
                )

            print(
                f"\nLoaded features: "
                f"{X.shape}"
            )

            if X.shape[1] != EXPECTED_TOTAL_FEATURES:

                print(
                    "\nWARNING:"
                )

                print(
                    f"Existing features "
                    f"contain {X.shape[1]} "
                    f"features."
                )

                print(
                    f"The current system "
                    f"requires "
                    f"{EXPECTED_TOTAL_FEATURES}."
                )

                return None, None, None

            return X, y, paths

    return None, None, None


# ============================================================
# REFERENCE ANGLES
# ============================================================

def calculate_reference_statistics(
    X,
    y
):
    """
    Calculate median angle values
    for every class.

    Feature structure:

    Left hand:
        coordinates = 0:63
        angles      = 63:73
        distances   = 73:85

    Right hand:
        coordinates = 85:148
        angles      = 148:158
        distances   = 158:170

    Pose:
        coordinates = 170:269
        angles      = 269:281
        distances   = 281:298

    Flags:
        298:302
    """

    print(
        "\nCalculating reference "
        "angle statistics..."
    )

    reference = {}

    classes = np.unique(
        y
    )

    for class_name in classes:

        class_features = X[
            y == class_name
        ]

        left_angles = (
            class_features[:, 63:73]
        )

        right_angles = (
            class_features[:, 148:158]
        )

        pose_angles = (
            class_features[:, 269:281]
        )

        reference[
            str(class_name)
        ] = {

            "left_hand_angles":
                np.median(
                    left_angles,
                    axis=0
                ).tolist(),

            "right_hand_angles":
                np.median(
                    right_angles,
                    axis=0
                ).tolist(),

            "pose_angles":
                np.median(
                    pose_angles,
                    axis=0
                ).tolist()
        }

    with open(
        REFERENCE_ANGLES_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            reference,
            file,
            indent=2
        )

    print(
        f"Reference angles saved to:\n"
        f"{REFERENCE_ANGLES_FILE}"
    )

    return reference


def load_reference_angles():

    if not REFERENCE_ANGLES_FILE.exists():

        return {}

    with open(
        REFERENCE_ANGLES_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(
            file
        )


# ============================================================
# MODEL TRAINING
# ============================================================

def train_models(
    X,
    y
):
    """
    Train multiple predefined ML algorithms.

    Models:
        SVM
        Random Forest
        KNN
        MLP

    The best model is selected
    using Macro F1.
    """

    print(
        "\n" + "=" * 70
    )

    print(
        "MODEL TRAINING"
    )

    print(
        "=" * 70
    )

    # --------------------------------------------------------
    # CHECK FEATURES
    # --------------------------------------------------------

    if X.shape[1] != EXPECTED_TOTAL_FEATURES:

        raise ValueError(
            f"Training requires "
            f"{EXPECTED_TOTAL_FEATURES} "
            f"features, but received "
            f"{X.shape[1]}."
        )

    # --------------------------------------------------------
    # LABEL ENCODER
    # --------------------------------------------------------

    label_encoder = LabelEncoder()

    y_encoded = (
        label_encoder.fit_transform(
            y
        )
    )

    classes = (
        label_encoder.classes_
    )

    print(
        f"\nNumber of classes: "
        f"{len(classes)}"
    )

    print(
        "\nClass labels:"
    )

    for index, class_name in enumerate(
        classes
    ):

        print(
            f"  {index}: {class_name}"
        )

    # --------------------------------------------------------
    # TRAIN / TEST SPLIT
    # --------------------------------------------------------

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y_encoded,
            test_size=0.20,
            random_state=42,
            stratify=y_encoded
        )
    )

    print(
        f"\nTraining samples: "
        f"{len(X_train)}"
    )

    print(
        f"Testing samples: "
        f"{len(X_test)}"
    )

    # --------------------------------------------------------
    # MODELS
    # --------------------------------------------------------

    models = {

        # ----------------------------------------------------
        # SVM
        # ----------------------------------------------------

        "SVM": Pipeline([

            (
                "scaler",
                StandardScaler()
            ),

            (
                "model",
                SVC(
                    kernel="rbf",
                    C=10,
                    gamma="scale",
                    probability=True,
                    class_weight="balanced",
                    random_state=42
                )
            )
        ]),

        # ----------------------------------------------------
        # RANDOM FOREST
        # ----------------------------------------------------

        "Random Forest": RandomForestClassifier(

            n_estimators=600,

            max_depth=None,

            min_samples_split=2,

            min_samples_leaf=1,

            max_features="sqrt",

            class_weight="balanced",

            random_state=42,

            n_jobs=-1
        ),

        # ----------------------------------------------------
        # KNN
        # ----------------------------------------------------

        "KNN": Pipeline([

            (
                "scaler",
                StandardScaler()
            ),

            (
                "model",
                KNeighborsClassifier(

                    n_neighbors=5,

                    weights="distance",

                    metric="euclidean"
                )
            )
        ]),

        # ----------------------------------------------------
        # MLP
        # ----------------------------------------------------

        "MLP": Pipeline([

            (
                "scaler",
                StandardScaler()
            ),

            (
                "model",
                MLPClassifier(

                    hidden_layer_sizes=(
                        256,
                        128,
                        64
                    ),

                    activation="relu",

                    solver="adam",

                    alpha=0.0001,

                    batch_size=32,

                    learning_rate="adaptive",

                    learning_rate_init=0.001,

                    max_iter=300,

                    early_stopping=True,

                    validation_fraction=0.15,

                    n_iter_no_change=20,

                    random_state=42
                )
            )
        ])
    }

    results = {}

    trained_models = {}

    best_model_name = None

    best_model = None

    best_f1 = -1

    # --------------------------------------------------------
    # TRAIN EACH MODEL
    # --------------------------------------------------------

    for model_name, model in models.items():

        print(
            "\n" + "-" * 70
        )

        print(
            f"Training {model_name}..."
        )

        print(
            "-" * 70
        )

        try:

            model.fit(
                X_train,
                y_train
            )

            predictions = (
                model.predict(
                    X_test
                )
            )

            accuracy = (
                accuracy_score(
                    y_test,
                    predictions
                )
            )

            macro_f1 = (
                f1_score(
                    y_test,
                    predictions,
                    average="macro",
                    zero_division=0
                )
            )

            weighted_f1 = (
                f1_score(
                    y_test,
                    predictions,
                    average="weighted",
                    zero_division=0
                )
            )

            print(
                f"Accuracy   : "
                f"{accuracy:.4f}"
            )

            print(
                f"Macro F1   : "
                f"{macro_f1:.4f}"
            )

            print(
                f"Weighted F1: "
                f"{weighted_f1:.4f}"
            )

            results[
                model_name
            ] = {

                "accuracy":
                    float(accuracy),

                "macro_f1":
                    float(macro_f1),

                "weighted_f1":
                    float(weighted_f1)
            }

            trained_models[
                model_name
            ] = model

            if macro_f1 > best_f1:

                best_f1 = macro_f1

                best_model_name = (
                    model_name
                )

                best_model = model

        except Exception as error:

            print(
                f"ERROR training "
                f"{model_name}: "
                f"{error}"
            )

    if best_model is None:

        print(
            "\nERROR: No model "
            "trained successfully."
        )

        return None

    # --------------------------------------------------------
    # SAVE LABEL ENCODER
    # --------------------------------------------------------

    joblib.dump(
        label_encoder,
        LABEL_ENCODER_FILE
    )

    # --------------------------------------------------------
    # SAVE BEST MODEL
    # --------------------------------------------------------

    joblib.dump(
        best_model,
        BEST_MODEL_FILE
    )

    # --------------------------------------------------------
    # SAVE RESULTS
    # --------------------------------------------------------

    with open(
        MODEL_RESULTS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            results,
            file,
            indent=2
        )

    # --------------------------------------------------------
    # BEST MODEL INFO
    # --------------------------------------------------------

    best_info = {

        "best_model":
            best_model_name,

        "selection_metric":
            "macro_f1",

        "best_macro_f1":
            float(best_f1),

        "feature_count":
            int(X.shape[1]),

        "class_count":
            int(len(classes)),

        "classes":
            classes.tolist(),

        "dataset_size":
            int(len(X)),

        "training_size":
            int(len(X_train)),

        "testing_size":
            int(len(X_test))
    }

    with open(
        BEST_MODEL_INFO_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            best_info,
            file,
            indent=2
        )

    # --------------------------------------------------------
    # MODEL COMPARISON
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "MODEL COMPARISON"
    )

    print(
        "=" * 70
    )

    for name, metrics in (
        results.items()
    ):

        print(
            f"\n{name}"
        )

        print(
            f"  Accuracy    : "
            f"{metrics['accuracy']:.4f}"
        )

        print(
            f"  Macro F1    : "
            f"{metrics['macro_f1']:.4f}"
        )

        print(
            f"  Weighted F1 : "
            f"{metrics['weighted_f1']:.4f}"
        )

    print(
        "\n" + "=" * 70
    )

    print(
        f"BEST MODEL: "
        f"{best_model_name}"
    )

    print(
        f"Best Macro F1: "
        f"{best_f1:.4f}"
    )

    print(
        "=" * 70
    )

    # --------------------------------------------------------
    # CLASSIFICATION REPORT
    # --------------------------------------------------------

    predictions = (
        best_model.predict(
            X_test
        )
    )

    report = classification_report(
        y_test,
        predictions,
        target_names=classes,
        zero_division=0
    )

    print(
        "\nClassification Report:\n"
    )

    print(
        report
    )

    with open(
        CLASSIFICATION_REPORT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            report
        )

    # --------------------------------------------------------
    # CONFUSION MATRIX
    # --------------------------------------------------------

    cm = confusion_matrix(
        y_test,
        predictions
    )

    plt.figure(
        figsize=(10, 8)
    )

    plt.imshow(cm)

    plt.title(
        f"Confusion Matrix - "
        f"{best_model_name}"
    )

    plt.xlabel(
        "Predicted"
    )

    plt.ylabel(
        "Actual"
    )

    plt.colorbar()

    plt.xticks(
        range(len(classes)),
        classes,
        rotation=90
    )

    plt.yticks(
        range(len(classes)),
        classes
    )

    plt.tight_layout()

    plt.savefig(
        CONFUSION_MATRIX_FILE,
        dpi=200
    )

    plt.close()

    # --------------------------------------------------------
    # REFERENCE ANGLES
    # --------------------------------------------------------

    calculate_reference_statistics(
        X,
        y
    )

    return best_model


# ============================================================
# LOAD TRAINED MODEL
# ============================================================

def load_trained_model():

    required = [

        BEST_MODEL_FILE,

        LABEL_ENCODER_FILE,

        BEST_MODEL_INFO_FILE
    ]

    for file in required:

        if not file.exists():

            return None

    model = joblib.load(
        BEST_MODEL_FILE
    )

    label_encoder = joblib.load(
        LABEL_ENCODER_FILE
    )

    with open(
        BEST_MODEL_INFO_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        model_info = json.load(
            file
        )

    model_feature_count = (
        get_model_expected_feature_count(
            model
        )
    )

    if model_feature_count != EXPECTED_TOTAL_FEATURES:

        print(
            "\nWARNING:"
        )

        print(
            f"Loaded model expects "
            f"{model_feature_count} "
            f"features."
        )

        print(
            f"Current system generates "
            f"{EXPECTED_TOTAL_FEATURES}."
        )

    return (
        model,
        label_encoder,
        model_info
    )


# ============================================================
# MODEL FEATURE COUNT
# ============================================================

def get_model_expected_feature_count(
    model
):
    """
    Detect the number of features
    expected by the trained model.
    """

    if hasattr(
        model,
        "n_features_in_"
    ):

        return int(
            model.n_features_in_
        )

    if hasattr(
        model,
        "named_steps"
    ):

        final_model = (
            model.named_steps.get(
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


# ============================================================
# PROBABILITY PREDICTION
# ============================================================

def get_prediction_probabilities(
    model,
    features,
    class_count
):
    """
    Get probability distribution.

    If the model does not support
    predict_proba(), a one-hot
    probability vector is returned.
    """

    features = np.asarray(
        features,
        dtype=np.float32
    )

    if features.ndim != 1:

        features = features.reshape(-1)

    expected_features = (
        get_model_expected_feature_count(
            model
        )
    )

    if (
        features.shape[0]
        != expected_features
    ):

        raise ValueError(
            f"Model expects "
            f"{expected_features} "
            f"features, but live "
            f"input contains "
            f"{features.shape[0]}."
        )

    x = features.reshape(
        1,
        -1
    )

    try:

        probabilities = (
            model.predict_proba(x)[0]
        )

        probabilities = np.asarray(
            probabilities,
            dtype=np.float32
        )

        if len(probabilities) == class_count:

            return probabilities

    except Exception:

        pass

    predicted = int(
        model.predict(x)[0]
    )

    probabilities = np.zeros(
        class_count,
        dtype=np.float32
    )

    if (
        0 <= predicted
        < class_count
    ):

        probabilities[
            predicted
        ] = 1.0

    return probabilities


# ============================================================
# TOP PREDICTIONS
# ============================================================

def get_top_predictions(
    model,
    label_encoder,
    features,
    top_n=3
):

    class_count = len(
        label_encoder.classes_
    )

    probabilities = (
        get_prediction_probabilities(
            model,
            features,
            class_count
        )
    )

    order = np.argsort(
        probabilities
    )[::-1]

    top_predictions = []

    for index in order[
        :top_n
    ]:

        class_name = (
            label_encoder
            .inverse_transform(
                [index]
            )[0]
        )

        confidence = (
            probabilities[index]
            * 100.0
        )

        top_predictions.append(
            (
                class_name,
                float(confidence)
            )
        )

    return top_predictions


# ============================================================
# ANGLES FROM FEATURE VECTOR
# ============================================================

def get_angles_from_features(
    features
):

    features = np.asarray(
        features,
        dtype=np.float32
    )

    left_angles = (
        features[63:73]
    )

    right_angles = (
        features[148:158]
    )

    pose_angles = (
        features[269:281]
    )

    return (
        left_angles,
        right_angles,
        pose_angles
    )


# ============================================================
# ANGLE COMPARISON
# ============================================================

def compare_angles(
    live_features,
    reference
):

    (
        live_left,
        live_right,
        live_pose
    ) = get_angles_from_features(
        live_features
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

    left_difference = (
        np.abs(
            live_left - ref_left
        )
    )

    right_difference = (
        np.abs(
            live_right - ref_right
        )
    )

    pose_difference = (
        np.abs(
            live_pose - ref_pose
        )
    )

    all_differences = (
        np.concatenate([
            left_difference,
            right_difference,
            pose_difference
        ])
    )

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
                overall_difference
                / 180.0,
                1.0
            )
        )
    )

    similarity = max(
        0.0,
        min(
            100.0,
            similarity
        )
    )

    return {

        "left_live":
            live_left,

        "right_live":
            live_right,

        "pose_live":
            live_pose,

        "left_reference":
            ref_left,

        "right_reference":
            ref_right,

        "pose_reference":
            ref_pose,

        "left_difference":
            left_difference,

        "right_difference":
            right_difference,

        "pose_difference":
            pose_difference,

        "overall_difference":
            overall_difference,

        "similarity":
            similarity
    }


# ============================================================
# DRAW LANDMARKS
# ============================================================

def draw_landmarks(
    frame,
    results
):

    # --------------------------------------------------------
    # BODY
    # --------------------------------------------------------

    if results.pose_landmarks:

        mp_drawing.draw_landmarks(

            frame,

            results.pose_landmarks,

            mp_holistic.POSE_CONNECTIONS,

            mp_drawing.DrawingSpec(
                thickness=2,
                circle_radius=2
            ),

            mp_drawing.DrawingSpec(
                thickness=2,
                circle_radius=2
            )
        )

    # --------------------------------------------------------
    # LEFT HAND
    # --------------------------------------------------------

    if results.left_hand_landmarks:

        mp_drawing.draw_landmarks(

            frame,

            results.left_hand_landmarks,

            mp_holistic.HAND_CONNECTIONS,

            mp_drawing.DrawingSpec(
                thickness=2,
                circle_radius=2
            ),

            mp_drawing.DrawingSpec(
                thickness=2,
                circle_radius=2
            )
        )

    # --------------------------------------------------------
    # RIGHT HAND
    # --------------------------------------------------------

    if results.right_hand_landmarks:

        mp_drawing.draw_landmarks(

            frame,

            results.right_hand_landmarks,

            mp_holistic.HAND_CONNECTIONS,

            mp_drawing.DrawingSpec(
                thickness=2,
                circle_radius=2
            ),

            mp_drawing.DrawingSpec(
                thickness=2,
                circle_radius=2
            )
        )


# ============================================================
# CHOOSE EXPECTED CLASS
# ============================================================

def choose_expected_class(
    label_encoder
):

    classes = (
        label_encoder.classes_
    )

    print(
        "\nAvailable classes:"
    )

    for index, class_name in enumerate(
        classes
    ):

        print(
            f"{index + 1}. "
            f"{class_name}"
        )

    print(
        "\nEnter expected class number."
    )

    print(
        "Enter 0 for automatic recognition."
    )

    while True:

        try:

            value = int(
                input(
                    "\nExpected class: "
                )
            )

            if value == 0:

                return None

            if (
                1 <= value
                <= len(classes)
            ):

                return classes[
                    value - 1
                ]

        except ValueError:

            pass

        print(
            "Invalid choice. "
            "Try again."
        )


# ============================================================
# DRAW TEXT WITH BACKGROUND
# ============================================================

def draw_text(
    frame,
    text,
    position,
    scale=0.7,
    color=(255, 255, 255),
    thickness=2
):
    """
    Draw readable text with
    a small dark background.
    """

    x, y = position

    (
        text_width,
        text_height
    ), baseline = cv2.getTextSize(
        text,
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        thickness
    )

    padding = 6

    cv2.rectangle(
        frame,

        (
            x - padding,
            y - text_height - padding
        ),

        (
            x + text_width + padding,
            y + baseline + padding
        ),

        (0, 0, 0),

        -1
    )

    cv2.putText(
        frame,
        text,
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        color,
        thickness,
        cv2.LINE_AA
    )


# ============================================================
# WEBCAM SYSTEM
# ============================================================

def run_webcam(
    model,
    label_encoder
):

    print(
        "\n" + "=" * 70
    )

    print(
        "LIVE WEBCAM RECOGNITION"
    )

    print(
        "=" * 70
    )

    reference_angles = (
        load_reference_angles()
    )

    expected_class = (
        choose_expected_class(
            label_encoder
        )
    )

    print(
        "\nStarting webcam..."
    )

    print(
        "\nControls:"
    )

    print(
        "  Q = Quit"
    )

    print(
        "  E = Change expected class"
    )

    print(
        "  R = Clear expected class"
    )

    # --------------------------------------------------------
    # MODEL FEATURE CHECK
    # --------------------------------------------------------

    model_feature_count = (
        get_model_expected_feature_count(
            model
        )
    )

    print(
        f"\nModel expects "
        f"{model_feature_count} features."
    )

    print(
        f"Live system generates "
        f"{EXPECTED_TOTAL_FEATURES} features."
    )

    if (
        model_feature_count
        != EXPECTED_TOTAL_FEATURES
    ):

        print(
            "\nERROR: Model and live "
            "feature configuration "
            "do not match."
        )

        return

    # --------------------------------------------------------
    # CAMERA
    # --------------------------------------------------------

    cap = cv2.VideoCapture(
        0
    )

    if not cap.isOpened():

        print(
            "\nERROR: Could not "
            "open webcam."
        )

        return

    cap.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        1280
    )

    cap.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        720
    )

    # --------------------------------------------------------
    # FULLSCREEN WINDOW
    # --------------------------------------------------------

    window_name = (
        "Classical Dance "
        "Mudra & Posture Recognition"
    )

    cv2.namedWindow(
        window_name,
        cv2.WINDOW_NORMAL
    )

    cv2.setWindowProperty(
        window_name,
        cv2.WND_PROP_FULLSCREEN,
        cv2.WINDOW_FULLSCREEN
    )

    # --------------------------------------------------------
    # PROBABILITY SMOOTHING
    # --------------------------------------------------------

    probability_history = deque(
        maxlen=12
    )

    stable_prediction = (
        "Detecting..."
    )

    stable_confidence = 0.0

    stable_similarity = 0.0

    no_detection_frames = 0

    # --------------------------------------------------------
    # MEDIAPIPE
    # --------------------------------------------------------

    with mp_holistic.Holistic(

        static_image_mode=False,

        model_complexity=1,

        enable_segmentation=False,

        refine_face_landmarks=False,

        min_detection_confidence=0.5,

        min_tracking_confidence=0.5

    ) as holistic:

        try:

            while True:

                success, frame = (
                    cap.read()
                )

                if not success:

                    continue

                # ------------------------------------------------
                # IMPORTANT:
                #
                # Keep RAW frame for MediaPipe/model.
                #
                # Do NOT flip before prediction.
                #
                # This maintains consistency with
                # the training images.
                # ------------------------------------------------

                frame_for_model = (
                    frame.copy()
                )

                frame_rgb = (
                    cv2.cvtColor(
                        frame_for_model,
                        cv2.COLOR_BGR2RGB
                    )
                )

                features, results = (
                    extract_features_from_rgb(
                        frame_rgb,
                        holistic
                    )
                )

                # ------------------------------------------------
                # DETECTION STATUS
                # ------------------------------------------------

                hands_detected = (
                    results.left_hand_landmarks
                    is not None
                    or
                    results.right_hand_landmarks
                    is not None
                )

                body_detected = (
                    results.pose_landmarks
                    is not None
                )

# Start prediction only when BOTH the body
# and at least one hand are detected.
#
# This prevents random predictions when the
# camera opens and the user has not made a
# dance pose yet.

                person_detected = (
                    body_detected
                    and hands_detected
                )

                # ------------------------------------------------
                # DRAW LANDMARKS ON RAW FRAME
                # ------------------------------------------------

                draw_landmarks(
                    frame_for_model,
                    results
                )

                # ------------------------------------------------
                # PREDICTION
                # ------------------------------------------------

                if person_detected:

                    no_detection_frames = 0

                    probabilities = (
                        get_prediction_probabilities(
                            model,
                            features,
                            len(
                                label_encoder.classes_
                            )
                        )
                    )

                    probability_history.append(
                        probabilities
                    )

                    average_probabilities = (
                        np.mean(
                            np.stack(
                                probability_history
                            ),
                            axis=0
                        )
                    )

                    predicted_index = int(
                        np.argmax(
                            average_probabilities
                        )
                    )

                    stable_prediction = (
                        label_encoder
                        .inverse_transform(
                            [predicted_index]
                        )[0]
                    )

                    stable_confidence = float(
                        average_probabilities[
                            predicted_index
                        ]
                        * 100.0
                    )

                else:

                    no_detection_frames += 1

                    if no_detection_frames > 8:

                        probability_history.clear()

                        stable_prediction = (
                            "Detecting..."
                        )

                        stable_confidence = 0.0

                        stable_similarity = 0.0

                # ------------------------------------------------
                # REFERENCE COMPARISON
                # ------------------------------------------------

                comparison = None

                if (
                    stable_prediction
                    != "Detecting..."
                ):

                    reference_class = (

                        expected_class

                        if expected_class
                        is not None

                        else stable_prediction
                    )

                    if (
                        reference_class
                        in reference_angles
                    ):

                        comparison = (
                            compare_angles(
                                features,
                                reference_angles[
                                    reference_class
                                ]
                            )
                        )

                        stable_similarity = float(
                            comparison[
                                "similarity"
                            ]
                        )

                # ------------------------------------------------
                # NATURAL MIRROR DISPLAY
                # ------------------------------------------------
                #
                # The model receives the original frame.
                #
                # Only the final annotated image is
                # flipped for natural selfie display.
                #
                # Text is drawn AFTER flipping.
                # Therefore text remains normal.
                # ------------------------------------------------

                display_frame = (
                    cv2.flip(
                        frame_for_model,
                        1
                    )
                )

                # ------------------------------------------------
                # UI
                # ------------------------------------------------

                if (
                    stable_prediction
                    == "Detecting..."
                ):

                    prediction_color = (
                        0,
                        255,
                        255
                    )

                else:

                    prediction_color = (
                        0,
                        255,
                        0
                    )

                draw_text(
                    display_frame,

                    f"Prediction: "
                    f"{stable_prediction}",

                    (25, 45),

                    scale=0.9,

                    color=prediction_color,

                    thickness=2
                )

                if (
                    stable_prediction
                    != "Detecting..."
                ):

                    draw_text(
                        display_frame,

                        f"Confidence: "
                        f"{stable_confidence:.1f}%",

                        (25, 85),

                        scale=0.7,

                        color=(
                            255,
                            255,
                            255
                        ),

                        thickness=2
                    )

                # ------------------------------------------------
                # EXPECTED CLASS
                # ------------------------------------------------

                if expected_class is not None:

                    draw_text(
                        display_frame,

                        f"Expected: "
                        f"{expected_class}",

                        (25, 130),

                        scale=0.7,

                        color=(
                            255,
                            255,
                            0
                        ),

                        thickness=2
                    )

                    if (
                        stable_prediction
                        == expected_class
                    ):

                        result_text = (
                            "MATCH"
                        )

                        result_color = (
                            0,
                            255,
                            0
                        )

                    elif (
                        stable_prediction
                        == "Detecting..."
                    ):

                        result_text = (
                            "DETECTING"
                        )

                        result_color = (
                            0,
                            255,
                            255
                        )

                    else:

                        result_text = (
                            "NOT MATCH"
                        )

                        result_color = (
                            0,
                            0,
                            255
                        )

                    draw_text(
                        display_frame,

                        f"Result: "
                        f"{result_text}",

                        (25, 170),

                        scale=0.7,

                        color=result_color,

                        thickness=2
                    )

                # ------------------------------------------------
                # SIMILARITY
                # ------------------------------------------------

                if comparison is not None:

                    draw_text(
                        display_frame,

                        f"Pose Similarity: "
                        f"{stable_similarity:.1f}%",

                        (25, 215),

                        scale=0.7,

                        color=(
                            0,
                            255,
                            255
                        ),

                        thickness=2
                    )

                # ------------------------------------------------
                # BOTTOM STATUS
                # ------------------------------------------------

                left_status = (

                    "Detected"

                    if results.left_hand_landmarks

                    else "Not detected"
                )

                right_status = (

                    "Detected"

                    if results.right_hand_landmarks

                    else "Not detected"
                )

                body_status = (

                    "Detected"

                    if results.pose_landmarks

                    else "Not detected"
                )

                bottom_y = (
                    display_frame.shape[0]
                    - 70
                )

                draw_text(
                    display_frame,

                    f"Left Hand: "
                    f"{left_status}",

                    (25, bottom_y),

                    scale=0.55,

                    color=(
                        255,
                        255,
                        255
                    ),

                    thickness=1
                )

                draw_text(
                    display_frame,

                    f"Right Hand: "
                    f"{right_status}",

                    (220, bottom_y),

                    scale=0.55,

                    color=(
                        255,
                        255,
                        255
                    ),

                    thickness=1
                )

                draw_text(
                    display_frame,

                    f"Body: "
                    f"{body_status}",

                    (430, bottom_y),

                    scale=0.55,

                    color=(
                        255,
                        255,
                        255
                    ),

                    thickness=1
                )

                draw_text(
                    display_frame,

                    "Q: Exit",

                    (
                        display_frame.shape[1]
                        - 130,
                        display_frame.shape[0]
                        - 25
                    ),

                    scale=0.55,

                    color=(
                        255,
                        255,
                        255
                    ),

                    thickness=1
                )

                # ------------------------------------------------
                # DISPLAY
                # ------------------------------------------------

                cv2.imshow(
                    window_name,
                    display_frame
                )

                key = (
                    cv2.waitKey(1)
                    & 0xFF
                )

                # ------------------------------------------------
                # QUIT
                # ------------------------------------------------

                if key == ord("q"):

                    break

                # ------------------------------------------------
                # CHANGE EXPECTED CLASS
                # ------------------------------------------------

                elif key == ord("e"):

                    expected_class = (
                        choose_expected_class(
                            label_encoder
                        )
                    )

                    probability_history.clear()

                # ------------------------------------------------
                # CLEAR EXPECTED CLASS
                # ------------------------------------------------

                elif key == ord("r"):

                    expected_class = None

                    probability_history.clear()

        finally:

            cap.release()

            cv2.destroyAllWindows()


# ============================================================
# MAIN MENU
# ============================================================

def main():

    print(
        "\n"
    )

    print(
        "=" * 70
    )

    print(
        " CLASSICAL INDIAN DANCE AI"
    )

    print(
        " MUDRA & POSTURE RECOGNITION SYSTEM"
    )

    print(
        "=" * 70
    )

    print(
        f"\nProject directory:\n"
        f"{PROJECT_DIR}"
    )

    print(
        f"\nDataset directory:\n"
        f"{DATASET_DIR}"
    )

    print(
        f"\nModel directory:\n"
        f"{MODEL_DIR}"
    )

    print(
        "\n" + "-" * 70
    )

    print(
        "1. Train new model"
    )

    print(
        "2. Use existing trained model"
    )

    print(
        "3. Retrain from existing extracted features"
    )

    print(
        "4. Exit"
    )

    print(
        "-" * 70
    )

    choice = input(
        "\nEnter your choice: "
    ).strip()

    # ========================================================
    # OPTION 1
    # TRAIN FROM DATASET
    # ========================================================

    if choice == "1":

        X, y, paths = (
            build_dataset()
        )

        if X is None:

            return

        train_models(
            X,
            y
        )

        loaded = (
            load_trained_model()
        )

        if loaded is None:

            print(
                "\nModel could not "
                "be loaded."
            )

            return

        (
            model,
            label_encoder,
            model_info
        ) = loaded

        print(
            "\nTraining completed "
            "successfully."
        )

        print(
            f"Best model: "
            f"{model_info['best_model']}"
        )

        print(
            f"Test Macro F1: "
            f"{model_info['best_macro_f1']:.4f}"
        )

        run_webcam(
            model,
            label_encoder
        )

    # ========================================================
    # OPTION 2
    # EXISTING MODEL
    # ========================================================

    elif choice == "2":

        loaded = (
            load_trained_model()
        )

        if loaded is None:

            print(
                "\nNo trained model found."
            )

            print(
                "\nPlease train the "
                "model first."
            )

            return

        (
            model,
            label_encoder,
            model_info
        ) = loaded

        print(
            f"\nLoaded model: "
            f"{model_info['best_model']}"
        )

        print(
            f"Classes: "
            f"{model_info['class_count']}"
        )

        print(
            f"Features: "
            f"{model_info['feature_count']}"
        )

        run_webcam(
            model,
            label_encoder
        )

    # ========================================================
    # OPTION 3
    # RETRAIN EXISTING FEATURES
    # ========================================================

    elif choice == "3":

        if not FEATURES_FILE.exists():

            print(
                "\nNo extracted "
                "features found."
            )

            print(
                "Choose option 1 first."
            )

            return

        data = np.load(
            FEATURES_FILE
        )

        X = data["X"]

        y = np.load(
            LABELS_FILE,
            allow_pickle=True
        )

        print(
            f"\nLoaded feature matrix: "
            f"{X.shape}"
        )

        if X.shape[1] != EXPECTED_TOTAL_FEATURES:

            print(
                "\nERROR:"
            )

            print(
                f"The saved feature "
                f"matrix contains "
                f"{X.shape[1]} features."
            )

            print(
                f"The current system "
                f"requires "
                f"{EXPECTED_TOTAL_FEATURES}."
            )

            print(
                "\nPlease choose "
                "Option 1 to rebuild "
                "the features."
            )

            return

        train_models(
            X,
            y
        )

    # ========================================================
    # OPTION 4
    # EXIT
    # ========================================================

    elif choice == "4":

        print(
            "\nExiting..."
        )

    else:

        print(
            "\nInvalid choice."
        )


# ============================================================
# PROGRAM START
# ============================================================

if __name__ == "__main__":

    main()