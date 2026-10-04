# AI-Powered Dance Gesture Recognition and Evaluation System

> An AI-powered web application for recognizing classical Indian dance gestures (Mudras) and evaluating dance performance using computer vision and machine learning.

---

## 📌 Overview

The **AI-Powered Dance Gesture Recognition and Evaluation System** is a computer-vision-based application designed to assist classical dance learners in practicing and improving their dance gestures.

Traditional dance evaluation can sometimes depend on manual observation, which may introduce subjectivity. This project aims to provide an AI-assisted approach by analyzing hand gestures and body posture from images or camera input and providing recognition results, confidence scores, and performance feedback.

The system combines **Computer Vision, Machine Learning, React.js, FastAPI, and MongoDB** into a complete full-stack application.

---

## 🎯 Objectives

* Recognize classical dance Mudras using AI and computer vision.
* Analyze hand landmarks and body posture.
* Provide predicted Mudra class and confidence score.
* Evaluate user performance against learned reference patterns.
* Provide an interactive practice environment.
* Maintain user practice history.
* Provide a platform for learning and practicing Mudras.
* Reduce subjectivity in manual gesture evaluation.

---

## ✨ Key Features

### 🤖 AI-Based Gesture Recognition

Recognizes classical dance gestures using extracted hand and body landmarks.

### 📷 Computer Vision Analysis

Uses **MediaPipe** and **OpenCV** to extract meaningful landmarks from dance images or camera input.

### 📊 Performance Evaluation

Provides recognition confidence and similarity-based evaluation to help users understand their performance.

### 🎯 Practice Mode

Users can practice gestures and receive AI-based feedback.

### 📚 Mudra Learning

Provides information about supported Mudras and helps users understand the gestures.

### 👤 User Authentication

Users can create accounts and access their personal practice experience.

### 📈 Practice History

Stores previous practice results so users can track their progress over time.

### 🗄️ MongoDB Integration

Stores user information and practice-related data using MongoDB Atlas.

### 🌐 Full-Stack Web Application

The project integrates a React frontend with a FastAPI backend and MongoDB database.

---

## 🧠 AI / Machine Learning

The recognition pipeline follows these major steps:

```text
Input Image / Camera
        ↓
Image Processing
        ↓
MediaPipe Landmark Detection
        ↓
Feature Extraction
        ↓
Machine Learning Model
        ↓
Mudra Prediction
        ↓
Confidence / Similarity Evaluation
        ↓
User Feedback
```

### Landmark-Based Feature Extraction

The system extracts features from:

* Left hand landmarks
* Right hand landmarks
* Body pose landmarks
* Landmark visibility and detection information
* Reference angle-based features

These features are processed and provided to machine-learning algorithms for classification.

### Machine Learning Algorithms

The project experiments with multiple classification approaches, including:

* Support Vector Machine (SVM)
* Random Forest
* K-Nearest Neighbors (KNN)
* Multi-Layer Perceptron (MLP)

The best-performing trained model is used for the final recognition pipeline.

---

## 💃 Supported Dance Gestures

The current dataset contains the following 10 gesture classes:

| #  | Mudra / Gesture |
| -- | --------------- |
| 1  | Alapadma        |
| 2  | Anjali          |
| 3  | Brahma          |
| 4  | Matsya          |
| 5  | Mushti          |
| 6  | Nataraja        |
| 7  | Parvathi        |
| 8  | Pataka          |
| 9  | Saraswathi      |
| 10 | Shivalinga      |

The dataset contains more than **2,000 labeled images** across these classes.

> The original dataset and trained model files are intentionally excluded from this public repository.

---

## 🏗️ System Architecture

```text
                    ┌──────────────────────┐
                    │      React.js        │
                    │      Frontend        │
                    └──────────┬───────────┘
                               │
                               │ HTTP / REST API
                               ▼
                    ┌──────────────────────┐
                    │       FastAPI        │
                    │       Backend        │
                    └──────────┬───────────┘
                               │
                 ┌─────────────┴─────────────┐
                 ▼                           ▼
        ┌─────────────────┐        ┌─────────────────┐
        │   ML Pipeline   │        │    MongoDB       │
        │ MediaPipe/OpenCV│        │      Atlas       │
        └─────────────────┘        └─────────────────┘
```

---

## 🛠️ Technology Stack

### Frontend

* React.js
* Vite
* JavaScript
* HTML5
* CSS3

### Backend

* Python
* FastAPI
* Uvicorn
* Pydantic
* PyMongo

### Artificial Intelligence / Computer Vision

* Python
* MediaPipe
* OpenCV
* Scikit-learn
* NumPy
* Pandas

### Database

* MongoDB Atlas

### Development Tools

* Git
* GitHub
* Visual Studio Code
* Python Virtual Environment

---

## 📁 Project Structure

```text
AI-Powered-Dance-Gesture-Recognition-and-Evaluation-System/
│
├── backend/
│   ├── main.py
│   ├── ml_service.py
│   ├── pose_evaluator.py
│   ├── requirements.txt
│   └── ...
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── context/
│   │   └── ...
│   ├── package.json
│   └── ...
│
├── dance_model.py
├── test_mongodb.py
├── .gitignore
├── LICENSE
└── README.md
```

> Dataset images, trained model artifacts, Mudra image assets, environment files, and other local/private resources are intentionally excluded from the repository.

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/PragnaMangi/AI-Powered-Dance-Gesture-Recognition-and-Evaluation-System.git
cd AI-Powered-Dance-Gesture-Recognition-and-Evaluation-System
```

### 2. Backend Setup

Create and activate a Python virtual environment:

```bash
python -m venv .venv
```

For Windows:

```powershell
.venv\Scripts\activate
```

Install the backend dependencies:

```bash
pip install -r backend/requirements.txt
```

### 3. Frontend Setup

Navigate to the frontend directory:

```bash
cd frontend
npm install
```

### 4. Environment Variables

Create a `.env` file for environment-specific configuration.

Example:

```env
MONGODB_URI=your_mongodb_connection_string
```

### 5. Start the Backend

From the project root:

```bash
uvicorn backend.main:app --reload
```

### 6. Start the Frontend

Open another terminal:

```bash
cd frontend
npm run dev
```

Open the local URL displayed by Vite in your browser.

---

## 🔐 Security & Repository Policy

Sensitive and large files are intentionally excluded from this public repository.

The `.gitignore` file excludes:

```text
.env
.venv/
node_modules/
dataset/
trained_model/
frontend/public/mudras/
```

This prevents:

* Private credentials from being exposed
* Large datasets from being uploaded
* Trained ML model artifacts from being publicly downloadable
* Local development files from being committed

> **Note:** The training dataset, trained model artifacts, and Mudra image assets are intentionally excluded from this public repository. The repository contains the complete application source code, machine learning pipeline, and implementation details.

---

## 📊 Dataset

The project was developed using a custom labeled image dataset containing more than **2,000 images** across 10 dance gesture classes.

The dataset was used for:

1. Image preprocessing
2. Landmark extraction
3. Feature generation
4. Model training
5. Model evaluation

The dataset itself is **not included in this public repository**.

---

## 🧪 Model Development

The model development workflow includes:

```text
Dataset
   ↓
Image Preprocessing
   ↓
Landmark Extraction
   ↓
Feature Engineering
   ↓
Train / Validation / Test
   ↓
Multiple ML Algorithms
   ↓
Model Evaluation
   ↓
Best Model Selection
   ↓
Prediction & Evaluation
```

Evaluation includes classification performance and confusion-matrix analysis.

---

## 🚀 Future Enhancements

Planned improvements include:

* Real-time camera-based gesture recognition
* Improved posture evaluation
* Additional classical dance gestures
* More advanced deep-learning models
* Personalized learning recommendations
* Progress visualization
* Advanced performance analytics
* Mobile-friendly experience
* Cloud deployment
* Improved multi-person pose analysis

---

## 🎓 Project Applications

This system can be useful for:

* Classical dance students
* Dance instructors
* Online dance learning platforms
* AI-assisted dance education
* Practice and self-evaluation
* Computer vision research
* Digital preservation of classical dance

---

## 👩‍💻 Developer

**Pragna Mangi**

B.Tech – Computer Science and Engineering
Specialization: Artificial Intelligence & Machine Learning

### Technical Interests

* Artificial Intelligence
* Machine Learning
* Computer Vision
* Generative AI
* Full-Stack Development

---

## 📄 License

This project is licensed under the **MIT License**.

See the [`LICENSE`](LICENSE) file for details.

---

## ⭐ Acknowledgement

This project combines concepts from **Artificial Intelligence, Computer Vision, Machine Learning, Full-Stack Development, and classical Indian dance** to explore how technology can support traditional art education and practice.

If you find this project interesting, consider giving the repository a ⭐ on GitHub.

---

## 📌 Version Information

**Version:** 1.0

**Last Updated:** October 2026

**Repository:** [AI-Powered-Dance-Gesture-Recognition-and-Evaluation-System](https://github.com/PragnaMangi/AI-Powered-Dance-Gesture-Recognition-and-Evaluation-System)
