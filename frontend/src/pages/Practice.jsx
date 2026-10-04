
import { useEffect, useRef, useState } from "react";
import axios from "axios";
import Navbar from "../components/Navbar";
import { useAuth } from "../context/AuthContext";

const API_URL = "http://127.0.0.1:8000";

function Practice() {
  // ============================================================
  // AUTHENTICATION
  // ============================================================

  const { user, token } = useAuth();

  // ============================================================
  // REFERENCES
  // ============================================================

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const timerRef = useRef(null);
  const busyRef = useRef(false);

  // ============================================================
  // SESSION SAVE REFERENCES
  // ============================================================

  const sessionSavedRef = useRef(false);

  // ============================================================
  // VOICE REFERENCES
  // ============================================================

  const voiceEnabledRef = useRef(false);
  const lastSpokenPredictionRef = useRef("");
  const lastSpokenTimeRef = useRef(0);
  const voicesRef = useRef([]);

  // ============================================================
  // STATE
  // ============================================================

  const [cameraStarted, setCameraStarted] = useState(false);

  const [status, setStatus] = useState("idle");

  const [result, setResult] = useState(null);

  const [error, setError] = useState("");

  const [voiceEnabled, setVoiceEnabled] = useState(false);

  // ============================================================
  // LOAD BROWSER VOICES
  // ============================================================

  useEffect(() => {
    if (!("speechSynthesis" in window)) {
      console.warn("Speech synthesis is not supported.");
      return;
    }

    const loadVoices = () => {
      const voices = window.speechSynthesis.getVoices();

      if (voices && voices.length > 0) {
        voicesRef.current = voices;

        console.log(
          "Speech voices loaded:",
          voices.map(
            (voice) => `${voice.name} (${voice.lang})`
          )
        );
      }
    };

    loadVoices();

    window.speechSynthesis.addEventListener(
      "voiceschanged",
      loadVoices
    );

    return () => {
      window.speechSynthesis.removeEventListener(
        "voiceschanged",
        loadVoices
      );
    };
  }, []);

  // ============================================================
  // GET ENGLISH VOICE
  // ============================================================

  const getEnglishVoice = () => {
    if (!("speechSynthesis" in window)) {
      return null;
    }

    let voices = voicesRef.current;

    if (!voices || voices.length === 0) {
      voices = window.speechSynthesis.getVoices();
      voicesRef.current = voices;
    }

    if (!voices || voices.length === 0) {
      return null;
    }

    const indianEnglish = voices.find(
      (voice) =>
        voice.lang &&
        voice.lang.toLowerCase() === "en-in"
    );

    if (indianEnglish) {
      return indianEnglish;
    }

    const usEnglish = voices.find(
      (voice) =>
        voice.lang &&
        voice.lang.toLowerCase() === "en-us"
    );

    if (usEnglish) {
      return usEnglish;
    }

    const ukEnglish = voices.find(
      (voice) =>
        voice.lang &&
        voice.lang.toLowerCase() === "en-gb"
    );

    if (ukEnglish) {
      return ukEnglish;
    }

    const englishVoice = voices.find(
      (voice) =>
        voice.lang &&
        voice.lang.toLowerCase().startsWith("en")
    );

    return englishVoice || voices[0];
  };

  // ============================================================
  // IMPROVEMENT FEEDBACK
  // ============================================================

  const getImprovementFeedback = (data) => {
    const prediction = data.prediction || "pose";

    const confidence = Number(
      data.confidence || 0
    );

    const similarity = Number(
      data.pose_similarity || 0
    );

    const leftHand = Boolean(
      data.left_hand_detected
    );

    const rightHand = Boolean(
      data.right_hand_detected
    );

    const bodyDetected = Boolean(
      data.body_detected
    );

    if (!bodyDetected) {
      return "Please move into the camera frame and make sure your full body is visible.";
    }

    if (!leftHand && !rightHand) {
      return "Please keep at least one hand clearly visible in front of the camera.";
    }

    if (similarity >= 90 && confidence >= 90) {
      return `${prediction} detected. Excellent pose. Your position is very accurate. Keep maintaining this posture.`;
    }

    if (similarity >= 80 && confidence >= 80) {
      return `${prediction} detected. Good pose. Your posture is close to the reference. Keep your hand position steady and improve your finger alignment slightly.`;
    }

    if (similarity >= 65 && confidence >= 60) {
      return `${prediction} detected. Your pose is partially correct. Try to improve your hand position, finger alignment, and body posture. Hold the pose steadily.`;
    }

    if (similarity < 65) {
      return `${prediction} detected, but the pose needs improvement. Check your hand shape, finger position, wrist angle, and body posture. Try the pose again slowly.`;
    }

    if (confidence < 60) {
      return `${prediction} detected with low confidence. Please make your hand gesture clearer and keep your entire pose steady.`;
    }

    return `${prediction} detected. Keep your posture steady and try to improve your hand and finger alignment.`;
  };

  // ============================================================
  // SPEAK TEXT
  // ============================================================

  const speakText = (text) => {
    if (!text) {
      return;
    }

    if (!voiceEnabledRef.current) {
      return;
    }

    if (!("speechSynthesis" in window)) {
      console.error(
        "Speech synthesis is not supported."
      );
      return;
    }

    const speakNow = () => {
      if (!voiceEnabledRef.current) {
        return;
      }

      const voice = getEnglishVoice();

      window.speechSynthesis.cancel();

      const utterance =
        new SpeechSynthesisUtterance(text);

      utterance.lang =
        voice?.lang || "en-IN";

      if (voice) {
        utterance.voice = voice;
      }

      utterance.volume = 1;
      utterance.rate = 0.85;
      utterance.pitch = 1;

      utterance.onstart = () => {
        console.log(
          "🔊 Voice started:",
          text
        );
      };

      utterance.onend = () => {
        console.log(
          "🔊 Voice completed."
        );
      };

      utterance.onerror = (event) => {
        console.error(
          "🔊 Speech error:",
          event.error
        );
      };

      window.speechSynthesis.speak(
        utterance
      );

      setTimeout(() => {
        if (
          voiceEnabledRef.current &&
          window.speechSynthesis.paused
        ) {
          window.speechSynthesis.resume();
        }
      }, 300);
    };

    const voices =
      window.speechSynthesis.getVoices();

    if (voices.length === 0) {
      console.log(
        "Waiting for browser speech voices..."
      );

      setTimeout(() => {
        speakNow();
      }, 500);
    } else {
      speakNow();
    }
  };

  // ============================================================
  // SPEAK DANCE FEEDBACK
  // ============================================================

  const speakFeedback = (data) => {
    if (!voiceEnabledRef.current) {
      return;
    }

    if (
      !data ||
      data.status !== "recognized" ||
      !data.prediction
    ) {
      return;
    }

    const prediction = data.prediction;

    const now = Date.now();

    const cooldown = 8000;

    const samePrediction =
      lastSpokenPredictionRef.current ===
      prediction;

    const tooSoon =
      now -
        lastSpokenTimeRef.current <
      cooldown;

    if (samePrediction && tooSoon) {
      return;
    }

    const feedback =
      getImprovementFeedback(data);

    console.log(
      "🗣️ Dance feedback:",
      feedback
    );

    lastSpokenPredictionRef.current =
      prediction;

    lastSpokenTimeRef.current = now;

    speakText(feedback);
  };

  // ============================================================
  // SAVE PRACTICE SESSION TO MONGODB
  // ============================================================

  const savePracticeSession = async (data) => {
    if (!token) {
      console.warn(
        "No authentication token available. Practice session will not be saved."
      );

      setError(
        "You are not logged in. Please log in again to save your practice session."
      );

      return;
    }

    if (
      !data ||
      data.status !== "recognized" ||
      !data.prediction
    ) {
      return;
    }

    const prediction = data.prediction;

    if (sessionSavedRef.current) {
      console.log(
        `Session already saved for this attempt: ${prediction}`
      );

      return;
    }

    const confidence = Number(
      data.confidence || 0
    );

    let score = 0;

    if (
      data.evaluation_details &&
      typeof data.evaluation_details ===
        "object"
    ) {
      score = Number(
        data.evaluation_details.score ??
          data.evaluation_details
            .overall_score ??
          data.evaluation_details
            .total_score ??
          0
      );
    }

    if (!score) {
      score = Number(
        data.score ??
          data.pose_similarity ??
          0
      );
    }

    score = Math.max(
      0,
      Math.min(100, score)
    );

    sessionSavedRef.current = true;

    console.log(
      "💾 Saving ONE authenticated practice session:",
      {
        user:
          user?.email ||
          user?.name ||
          "Authenticated user",

        pose: prediction,

        confidence,

        score,
      }
    );

    try {
      const response = await axios.post(
        `${API_URL}/sessions`,
        {
          pose: prediction,

          confidence: confidence,

          score: score,

          status: "Practice",
        },
        {
          headers: {
            Authorization:
              `Bearer ${token}`,
          },

          timeout: 10000,
        }
      );

      console.log(
        "✅ Authenticated practice session saved:",
        response.data
      );
    } catch (err) {
      console.error(
        "❌ Failed to save authenticated practice session:",
        err
      );

      sessionSavedRef.current = false;

      if (err.response?.status === 401) {
        setError(
          "Your login session has expired. Please log in again."
        );
      } else if (
        err.response?.data?.detail
      ) {
        setError(
          err.response.data.detail
        );
      } else {
        setError(
          "Practice was recognized, but the session could not be saved."
        );
      }
    }
  };

  // ============================================================
  // TOGGLE VOICE
  // ============================================================

  const toggleVoice = () => {
    if (voiceEnabled) {
      voiceEnabledRef.current = false;

      setVoiceEnabled(false);

      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }

      lastSpokenPredictionRef.current = "";
      lastSpokenTimeRef.current = 0;

      console.log(
        "🔇 Voice feedback OFF"
      );
    } else {
      voiceEnabledRef.current = true;

      setVoiceEnabled(true);

      lastSpokenPredictionRef.current = "";
      lastSpokenTimeRef.current = 0;

      console.log(
        "🔊 Voice feedback ON"
      );

      speakText(
        "Voice feedback is now enabled."
      );
    }
  };

  // ============================================================
  // START CAMERA
  // ============================================================

  const startCamera = async () => {
    try {
      setError("");

      setResult(null);

      setStatus("waiting");

      sessionSavedRef.current = false;

      lastSpokenPredictionRef.current = "";
      lastSpokenTimeRef.current = 0;

      const stream =
        await navigator.mediaDevices.getUserMedia(
          {
            video: {
              width: {
                ideal: 640,
              },

              height: {
                ideal: 480,
              },

              facingMode: "user",
            },

            audio: false,
          }
        );

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject =
          stream;

        await videoRef.current.play();
      }

      setCameraStarted(true);
    } catch (err) {
      console.error(
        "Camera error:",
        err
      );

      setError(
        "Camera access was denied or the camera is unavailable."
      );

      setCameraStarted(false);

      setStatus("idle");
    }
  };

  // ============================================================
  // STOP CAMERA
  // ============================================================

  const stopCamera = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);

      timerRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current
        .getTracks()
        .forEach((track) =>
          track.stop()
        );

      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }

    setCameraStarted(false);

    setStatus("idle");

    setResult(null);

    setError("");

    busyRef.current = false;

    sessionSavedRef.current = false;

    lastSpokenPredictionRef.current = "";
    lastSpokenTimeRef.current = 0;
  };

  // ============================================================
  // CAPTURE FRAME AND PREDICT
  // ============================================================

  const captureAndPredict = async () => {
    if (busyRef.current) {
      return;
    }

    if (
      !videoRef.current ||
      !canvasRef.current
    ) {
      return;
    }

    if (
      videoRef.current.readyState < 2
    ) {
      return;
    }

    busyRef.current = true;

    try {
      const video = videoRef.current;

      const canvas = canvasRef.current;

      canvas.width =
        video.videoWidth || 640;

      canvas.height =
        video.videoHeight || 480;

      const context =
        canvas.getContext("2d");

      if (!context) {
        return;
      }

      context.drawImage(
        video,
        0,
        0,
        canvas.width,
        canvas.height
      );

      const blob =
        await new Promise(
          (resolve) => {
            canvas.toBlob(
              (imageBlob) =>
                resolve(imageBlob),

              "image/jpeg",

              0.75
            );
          }
        );

      if (!blob) {
        return;
      }

      const formData = new FormData();

      formData.append(
        "file",
        blob,
        "dance-frame.jpg"
      );

      const response =
        await axios.post(
          `${API_URL}/predict`,
          formData,
          {
            headers: {
              "Content-Type":
                "multipart/form-data",
            },

            timeout: 10000,
          }
        );

      const data = response.data;

      console.log(
        "AI Response:",
        data
      );

      // ======================================================
      // WAITING
      // ======================================================

      if (data.status === "waiting") {
        setStatus("waiting");

        setResult(null);

        setError("");

        if (
          sessionSavedRef.current
        ) {
          console.log(
            "🔓 Previous pose ended. New pose can now be saved."
          );
        }

        sessionSavedRef.current = false;
      }

      // ======================================================
      // RECOGNIZED
      // ======================================================

      else if (
        data.status === "recognized" &&
        data.prediction
      ) {
        setStatus("recognized");

        setResult(data);

        setError("");

        speakFeedback(data);

        savePracticeSession(data);
      }

      // ======================================================
      // DETECTING
      // ======================================================

      else {
        setStatus("detecting");

        setResult(null);

        setError("");
      }
    } catch (err) {
      console.error(
        "Prediction error:",
        err
      );

      if (err.response) {
        setError(
          `Backend error: ${err.response.status}`
        );
      } else if (
        err.code === "ECONNABORTED"
      ) {
        setError(
          "AI request timed out. Please try again."
        );
      } else {
        setError(
          "Could not connect to the AI backend."
        );
      }
    } finally {
      busyRef.current = false;
    }
  };

  // ============================================================
  // PREDICTION LOOP
  // ============================================================

  useEffect(() => {
    if (!cameraStarted) {
      return;
    }

    timerRef.current = setInterval(() => {
      captureAndPredict();
    }, 1200);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);

        timerRef.current = null;
      }
    };
  }, [cameraStarted]);

  // ============================================================
  // CLEANUP
  // ============================================================

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }

      if (streamRef.current) {
        streamRef.current
          .getTracks()
          .forEach((track) =>
            track.stop()
          );
      }

      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  // ============================================================
  // STATUS TITLE
  // ============================================================

  const getStatusTitle = () => {
    if (status === "idle") {
      return "Camera Ready";
    }

    if (status === "waiting") {
      return "Waiting for Pose";
    }

    if (status === "detecting") {
      return "Detecting...";
    }

    if (status === "recognized") {
      return "Pose Recognized";
    }

    return "Ready";
  };

  // ============================================================
  // STATUS MESSAGE
  // ============================================================

  const getStatusMessage = () => {
    if (status === "idle") {
      return "Start the camera when you are ready.";
    }

    if (status === "waiting") {
      return "Position yourself in front of the camera.";
    }

    if (status === "detecting") {
      return "Analyzing your dance pose...";
    }

    if (status === "recognized") {
      return "Your pose has been recognized.";
    }

    return "";
  };

  // ============================================================
  // UI
  // ============================================================

  return (
    <div className="practice-page">

      {/* ======================================================
          SHARED NAVIGATION
      ====================================================== */}

      <Navbar />

      {/* ======================================================
          MAIN
      ====================================================== */}

      <main className="practice-container">

        {/* ====================================================
            CAMERA
        ==================================================== */}

        <section className="camera-section">

          <div className="camera-card">

            <div className="camera-header">

              <div>
                <span className="small-label">
                  AI CAMERA
                </span>

                <h2>
                  Practice your mudra
                </h2>
              </div>

              <div
                className={`status-badge ${status}`}
              >
                <span></span>

                {getStatusTitle()}
              </div>

            </div>

            <div className="camera-wrapper">

              <video
                ref={videoRef}
                className="camera-video"
                autoPlay
                playsInline
                muted
              />

              {!cameraStarted && (
                <div className="camera-overlay">

                  <div className="camera-icon">
                    📷
                  </div>

                  <h3>
                    Camera is not started
                  </h3>

                  <p>
                    Start the camera and stand where your
                    full body and hands are visible.
                  </p>

                </div>
              )}

              {cameraStarted &&
                status === "waiting" && (
                  <div className="camera-guidance">

                    <div className="guidance-box">

                      <strong>
                        Position yourself
                      </strong>

                      <span>
                        Make sure your body and at least
                        one hand are visible.
                      </span>

                    </div>

                  </div>
                )}

              {cameraStarted &&
                status === "detecting" && (
                  <div className="camera-guidance">

                    <div className="guidance-box">

                      <strong>
                        Detecting pose...
                      </strong>

                      <span>
                        Hold your dance position.
                      </span>

                    </div>

                  </div>
                )}

              {cameraStarted &&
                status === "recognized" &&
                result?.prediction && (
                  <div className="prediction-overlay">

                    <span>
                      DETECTED MUDRA
                    </span>

                    <strong>
                      {result.prediction}
                    </strong>

                  </div>
                )}

            </div>

            <canvas
              ref={canvasRef}
              style={{
                display: "none",
              }}
            />

            {/* ==================================================
                CAMERA CONTROL

                Start Camera is kept BELOW the camera.
                It changes to Stop Camera after starting.
            ================================================== */}

            <div className="camera-controls">

              {!cameraStarted ? (
                <button
                  className="start-button"
                  onClick={startCamera}
                >
                  Start Camera
                </button>
              ) : (
                <button
                  className="stop-button"
                  onClick={stopCamera}
                >
                  Stop Camera
                </button>
              )}

            </div>

            {/* ==================================================
                VOICE TOGGLE
            ================================================== */}

            <div
              style={{
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                marginTop: "15px",
              }}
            >

              <button
                onClick={toggleVoice}
                style={{
                  padding: "11px 20px",
                  borderRadius: "10px",
                  border: "none",
                  cursor: "pointer",
                  fontSize: "14px",
                  fontWeight: "600",
                  background: voiceEnabled
                    ? "#16a34a"
                    : "#6b7280",
                  color: "white",
                  transition: "0.2s",
                  minWidth: "200px",
                }}
              >
                {voiceEnabled
                  ? "🔊 Voice Feedback ON"
                  : "🔇 Voice Feedback OFF"}
              </button>

            </div>

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

          </div>

        </section>

        {/* ====================================================
            RESULTS
        ==================================================== */}

        <aside className="results-section">

          <div className="result-card">

            <span className="small-label">
              AI ANALYSIS
            </span>

            <h2>
              {getStatusTitle()}
            </h2>

            <p className="result-message">
              {getStatusMessage()}
            </p>

            {result?.status === "recognized" ? (
              <>

                <div className="main-prediction">

                  <span>
                    Recognized Mudra
                  </span>

                  <strong>
                    {result.prediction}
                  </strong>

                </div>

                <div className="metrics">

                  <div className="metric">

                    <span>
                      Model Confidence
                    </span>

                    <strong>
                      {result.confidence}%
                    </strong>

                  </div>

                  <div className="metric">

                    <span>
                      Pose Similarity
                    </span>

                    <strong>
                      {result.pose_similarity}%
                    </strong>

                  </div>

                </div>

                <div className="detection-info">

                  <h3>
                    Detection
                  </h3>

                  <div>

                    <span>
                      Body
                    </span>

                    <b>
                      {result.body_detected
                        ? "Detected ✓"
                        : "Not detected"}
                    </b>

                  </div>

                  <div>

                    <span>
                      Left Hand
                    </span>

                    <b>
                      {result.left_hand_detected
                        ? "Detected ✓"
                        : "Not detected"}
                    </b>

                  </div>

                  <div>

                    <span>
                      Right Hand
                    </span>

                    <b>
                      {result.right_hand_detected
                        ? "Detected ✓"
                        : "Not detected"}
                    </b>

                  </div>

                </div>

                {result.top_predictions?.length >
                  0 && (
                  <div className="top-predictions">

                    <h3>
                      Other possibilities
                    </h3>

                    {result.top_predictions
                      .slice(1)
                      .map(
                        (item, index) => (
                          <div
                            className="prediction-row"
                            key={index}
                          >

                            <span>
                              {item.label}
                            </span>

                            <span>
                              {item.confidence}%
                            </span>

                          </div>
                        )
                      )}

                  </div>
                )}

              </>
            ) : (

              <div className="waiting-panel">

                {/* SAME LOGO AS MAIN NAVBAR */}

                <div className="waiting-logo">
                  <span className="logo-icon">
                    ✦
                  </span>
                </div>

                <h3>
                  Waiting for you
                </h3>

                <p>
                  Stand in front of the camera and perform
                  a classical dance mudra.
                </p>

              </div>

            )}

          </div>

          {/* ==================================================
              PRACTICE TIP
          ================================================== */}

          <div className="practice-tip">

            <span>
              💡
            </span>

            <div>

              <strong>
                Practice Tip
              </strong>

              <p>
                Keep your hands clearly visible and maintain
                the pose for a few seconds for better
                recognition.
              </p>

            </div>

          </div>

        </aside>

      </main>

    </div>
  );
}

export default Practice;