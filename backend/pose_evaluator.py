# ============================================================
# POSE EVALUATOR
# Classical Indian Dance Pose & Mudra Evaluation
# ============================================================

from pathlib import Path
import json
import numpy as np


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent

REFERENCE_FILE = (
    PROJECT_DIR
    / "trained_model"
    / "reference_angles.json"
)


# ============================================================
# FEATURE POSITIONS
# ============================================================

LEFT_HAND_ANGLES = slice(63, 73)

RIGHT_HAND_ANGLES = slice(148, 158)

POSE_ANGLES = slice(269, 281)


# ============================================================
# POSE EVALUATOR
# ============================================================

class PoseEvaluator:

    def __init__(self):

        self.reference_file = REFERENCE_FILE

        self.reference_angles = (
            self.load_reference_angles()
        )

    # ========================================================
    # LOAD REFERENCE DATA
    # ========================================================

    def load_reference_angles(self):

        if not self.reference_file.exists():

            raise FileNotFoundError(
                f"Reference angle file not found:\n"
                f"{self.reference_file}"
            )

        with open(
            self.reference_file,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if not isinstance(data, dict):

            raise ValueError(
                "reference_angles.json does not contain "
                "a valid dictionary."
            )

        return data

    # ========================================================
    # GET AVAILABLE CLASSES
    # ========================================================

    def get_available_classes(self):

        return list(
            self.reference_angles.keys()
        )

    # ========================================================
    # GET ANGLES FROM FEATURES
    # ========================================================

    def get_angles_from_features(
        self,
        features
    ):

        features = np.asarray(
            features,
            dtype=np.float32
        ).reshape(-1)

        if len(features) < 302:

            raise ValueError(
                f"Expected 302 features, "
                f"but received {len(features)}."
            )

        left_angles = features[
            LEFT_HAND_ANGLES
        ]

        right_angles = features[
            RIGHT_HAND_ANGLES
        ]

        pose_angles = features[
            POSE_ANGLES
        ]

        return (
            left_angles,
            right_angles,
            pose_angles
        )

    # ========================================================
    # ANGLE DIFFERENCE
    # ========================================================

    def calculate_angle_difference(
        self,
        live,
        reference
    ):

        live = np.asarray(
            live,
            dtype=np.float32
        )

        reference = np.asarray(
            reference,
            dtype=np.float32
        )

        size = min(
            len(live),
            len(reference)
        )

        if size == 0:

            return np.array(
                [],
                dtype=np.float32
            )

        live = live[:size]

        reference = reference[:size]

        return np.abs(
            live - reference
        )

    # ========================================================
    # SIMILARITY
    # ========================================================

    def calculate_similarity(
        self,
        differences
    ):

        differences = np.asarray(
            differences,
            dtype=np.float32
        )

        if differences.size == 0:

            return 0.0

        average_difference = float(
            np.mean(differences)
        )

        similarity = (
            100.0
            * (
                1.0
                - min(
                    average_difference / 180.0,
                    1.0
                )
            )
        )

        return float(
            max(
                0.0,
                min(
                    100.0,
                    similarity
                )
            )
        )

    # ========================================================
    # HAND FEEDBACK
    # ========================================================

    def generate_hand_feedback(
        self,
        differences,
        hand_name
    ):

        if differences.size == 0:

            return []

        average_difference = float(
            np.mean(differences)
        )

        maximum_difference = float(
            np.max(differences)
        )

        feedback = []

        if average_difference <= 8:

            feedback.append(
                f"Your {hand_name} hand shape "
                f"is very close to the reference."
            )

        elif average_difference <= 15:

            feedback.append(
                f"Slightly improve your "
                f"{hand_name} hand and finger alignment."
            )

        elif average_difference <= 25:

            feedback.append(
                f"Improve your {hand_name} "
                f"hand shape and finger positioning."
            )

        else:

            feedback.append(
                f"Your {hand_name} hand shape "
                f"needs more correction."
            )

        if maximum_difference > 40:

            feedback.append(
                f"Pay closer attention to the "
                f"{hand_name} wrist and finger positioning."
            )

        elif maximum_difference > 25:

            feedback.append(
                f"Adjust your {hand_name} "
                f"hand position slightly."
            )

        return feedback

    # ========================================================
    # BODY FEEDBACK
    # ========================================================

    def generate_body_feedback(
        self,
        differences
    ):

        if differences.size == 0:

            return []

        average_difference = float(
            np.mean(differences)
        )

        maximum_difference = float(
            np.max(differences)
        )

        feedback = []

        if average_difference <= 8:

            feedback.append(
                "Your body posture closely "
                "matches the reference."
            )

        elif average_difference <= 15:

            feedback.append(
                "Slightly adjust your body "
                "posture to match the reference."
            )

        elif average_difference <= 25:

            feedback.append(
                "Improve your body posture "
                "and overall alignment."
            )

        else:

            feedback.append(
                "Your body posture needs "
                "more correction."
            )

        if maximum_difference > 40:

            feedback.append(
                "Pay closer attention to your "
                "upper-body and leg alignment."
            )

        elif maximum_difference > 25:

            feedback.append(
                "Adjust your body position "
                "slightly to match the reference."
            )

        return feedback

    # ========================================================
    # MAIN EVALUATION
    # ========================================================

    def evaluate_pose(
        self,
        features,
        prediction,
        left_hand_detected=True,
        right_hand_detected=True,
        body_detected=True
    ):

        result = {

            "prediction": prediction,

            "similarity": 0.0,

            "feedback": [],

            "details": {

                "left_hand_difference": 0.0,

                "right_hand_difference": 0.0,

                "body_difference": 0.0
            }
        }

        # ----------------------------------------------------
        # BODY CHECK
        # ----------------------------------------------------

        if not body_detected:

            result["feedback"] = [
                "Please move into the camera frame.",
                "Keep your full body visible."
            ]

            return result

        # ----------------------------------------------------
        # HAND CHECK
        # ----------------------------------------------------

        if (
            not left_hand_detected
            and not right_hand_detected
        ):

            result["feedback"] = [
                "Your body is detected, "
                "but your hands are not clear.",
                "Bring your hands into the camera view."
            ]

            return result

        # ----------------------------------------------------
        # REFERENCE CHECK
        # ----------------------------------------------------

        if prediction not in self.reference_angles:

            result["feedback"] = [
                "Reference data for this pose "
                "is not available."
            ]

            return result

        reference = self.reference_angles[
            prediction
        ]

        # ----------------------------------------------------
        # LIVE ANGLES
        # ----------------------------------------------------

        (
            live_left,
            live_right,
            live_pose
        ) = self.get_angles_from_features(
            features
        )

        # ----------------------------------------------------
        # REFERENCE ANGLES
        # ----------------------------------------------------

        reference_left = np.asarray(
            reference.get(
                "left_hand_angles",
                []
            ),
            dtype=np.float32
        )

        reference_right = np.asarray(
            reference.get(
                "right_hand_angles",
                []
            ),
            dtype=np.float32
        )

        reference_pose = np.asarray(
            reference.get(
                "pose_angles",
                []
            ),
            dtype=np.float32
        )

        # ----------------------------------------------------
        # LEFT HAND
        # ----------------------------------------------------

        if left_hand_detected:

            left_difference = (
                self.calculate_angle_difference(
                    live_left,
                    reference_left
                )
            )

        else:

            left_difference = np.array(
                [],
                dtype=np.float32
            )

        # ----------------------------------------------------
        # RIGHT HAND
        # ----------------------------------------------------

        if right_hand_detected:

            right_difference = (
                self.calculate_angle_difference(
                    live_right,
                    reference_right
                )
            )

        else:

            right_difference = np.array(
                [],
                dtype=np.float32
            )

        # ----------------------------------------------------
        # BODY
        # ----------------------------------------------------

        pose_difference = (
            self.calculate_angle_difference(
                live_pose,
                reference_pose
            )
        )

        # ----------------------------------------------------
        # COLLECT DIFFERENCES
        # ----------------------------------------------------

        all_differences = []

        if left_difference.size > 0:

            all_differences.extend(
                left_difference.tolist()
            )

        if right_difference.size > 0:

            all_differences.extend(
                right_difference.tolist()
            )

        if pose_difference.size > 0:

            all_differences.extend(
                pose_difference.tolist()
            )

        # ----------------------------------------------------
        # SIMILARITY
        # ----------------------------------------------------

        similarity = (
            self.calculate_similarity(
                all_differences
            )
        )

        # ----------------------------------------------------
        # FEEDBACK
        # ----------------------------------------------------

        feedback = []

        if left_hand_detected:

            feedback.extend(
                self.generate_hand_feedback(
                    left_difference,
                    "left"
                )
            )

        if right_hand_detected:

            feedback.extend(
                self.generate_hand_feedback(
                    right_difference,
                    "right"
                )
            )

        feedback.extend(
            self.generate_body_feedback(
                pose_difference
            )
        )

        # ----------------------------------------------------
        # REMOVE DUPLICATES
        # ----------------------------------------------------

        unique_feedback = []

        for message in feedback:

            if message not in unique_feedback:

                unique_feedback.append(
                    message
                )

        # ----------------------------------------------------
        # OVERALL MESSAGE
        # ----------------------------------------------------

        if similarity >= 92:

            unique_feedback.insert(
                0,
                "Excellent. Your pose closely "
                "matches the reference."
            )

        elif similarity >= 82:

            unique_feedback.insert(
                0,
                "Very good. Your pose is close "
                "to the reference."
            )

        elif similarity >= 70:

            unique_feedback.insert(
                0,
                "Your pose is good, but a few "
                "adjustments are needed."
            )

        else:

            unique_feedback.insert(
                0,
                "Your pose needs improvement. "
                "Focus on the corrections below."
            )

        unique_feedback = unique_feedback[:5]

        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        result["similarity"] = round(
            similarity,
            2
        )

        result["feedback"] = (
            unique_feedback
        )

        result["details"] = {

            "left_hand_difference": round(
                float(
                    np.mean(
                        left_difference
                    )
                )
                if left_difference.size > 0
                else 0.0,
                2
            ),

            "right_hand_difference": round(
                float(
                    np.mean(
                        right_difference
                    )
                )
                if right_difference.size > 0
                else 0.0,
                2
            ),

            "body_difference": round(
                float(
                    np.mean(
                        pose_difference
                    )
                )
                if pose_difference.size > 0
                else 0.0,
                2
            )
        }

        return result


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("POSE EVALUATOR TEST")
    print("=" * 60)

    try:

        evaluator = PoseEvaluator()

        classes = (
            evaluator.get_available_classes()
        )

        print(
            f"\nReference file:"
            f"\n{REFERENCE_FILE}"
        )

        print(
            f"\nReference classes found: "
            f"{len(classes)}"
        )

        print("\nClasses:")

        for class_name in classes:

            print(
                f"  - {class_name}"
            )

        print(
            "\nPoseEvaluator class loaded successfully."
        )

        print(
            "✅ Pose evaluator is ready."
        )

    except Exception as error:

        print(
            "\n❌ Pose evaluator test failed:"
        )

        print(error)