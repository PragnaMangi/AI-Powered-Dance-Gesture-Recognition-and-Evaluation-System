
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Navbar from "../components/Navbar";

const API_URL = "http://127.0.0.1:8000";

function History() {
  const { token } = useAuth();

  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // ============================================================
  // LOAD PRACTICE HISTORY
  // ============================================================

  useEffect(() => {
    if (token) {
      fetchSessions();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchSessions = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await fetch(
        `${API_URL}/sessions`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.status === 401) {
        throw new Error(
          "Your login session has expired. Please login again."
        );
      }

      if (!response.ok) {
        throw new Error(
          "Could not load practice history."
        );
      }

      const data = await response.json();

      setSessions(data.sessions || []);
    } catch (err) {
      console.error(
        "History loading error:",
        err
      );

      setError(
        err.message ||
          "Unable to load practice history. Please make sure the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // DATE FORMAT
  // ============================================================

  const formatDate = (dateString) => {
    if (!dateString) {
      return {
        date: "Unknown",
        time: "",
      };
    }

    /*
     * Backend stores the time in UTC.
     *
     * Example:
     * 2026-09-24T11:06:30.281000
     *
     * Add Z so JavaScript knows this is UTC.
     */

    let utcDateString = dateString;

    if (
      !dateString.endsWith("Z") &&
      !dateString.includes("+")
    ) {
      utcDateString = `${dateString}Z`;
    }

    const date = new Date(utcDateString);

    if (Number.isNaN(date.getTime())) {
      return {
        date: "Unknown",
        time: "",
      };
    }

    // ----------------------------------------------------------
    // Convert to India Standard Time
    // ----------------------------------------------------------

    const indiaDateFormatter =
      new Intl.DateTimeFormat(
        "en-IN",
        {
          timeZone: "Asia/Kolkata",
          day: "2-digit",
          month: "short",
          year: "numeric",
        }
      );

    const indiaTimeFormatter =
      new Intl.DateTimeFormat(
        "en-IN",
        {
          timeZone: "Asia/Kolkata",
          hour: "2-digit",
          minute: "2-digit",
          hour12: true,
        }
      );

    // ----------------------------------------------------------
    // Determine Today / Yesterday using IST
    // ----------------------------------------------------------

    const dateParts =
      new Intl.DateTimeFormat(
        "en-IN",
        {
          timeZone: "Asia/Kolkata",
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
        }
      ).formatToParts(date);

    const now = new Date();

    const nowParts =
      new Intl.DateTimeFormat(
        "en-IN",
        {
          timeZone: "Asia/Kolkata",
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
        }
      ).formatToParts(now);

    const getPart = (parts, type) => {
      const part = parts.find(
        (item) => item.type === type
      );

      return part ? part.value : "";
    };

    const sessionYear = getPart(
      dateParts,
      "year"
    );

    const sessionMonth = getPart(
      dateParts,
      "month"
    );

    const sessionDay = getPart(
      dateParts,
      "day"
    );

    const currentYear = getPart(
      nowParts,
      "year"
    );

    const currentMonth = getPart(
      nowParts,
      "month"
    );

    const currentDay = getPart(
      nowParts,
      "day"
    );

    const sessionDateOnly =
      new Date(
        `${sessionYear}-${sessionMonth}-${sessionDay}T00:00:00`
      );

    const todayDateOnly =
      new Date(
        `${currentYear}-${currentMonth}-${currentDay}T00:00:00`
      );

    const difference =
      Math.round(
        (
          todayDateOnly -
          sessionDateOnly
        ) /
          (1000 * 60 * 60 * 24)
      );

    let formattedDate;

    if (difference === 0) {
      formattedDate = "Today";
    } else if (difference === 1) {
      formattedDate = "Yesterday";
    } else {
      formattedDate =
        indiaDateFormatter.format(date);
    }

    const formattedTime =
      indiaTimeFormatter.format(date);

    return {
      date: formattedDate,
      time: formattedTime,
    };
  };

  // ============================================================
  // HISTORY CALCULATIONS
  // ============================================================

  const totalSessions = sessions.length;

  const averageScore =
    totalSessions > 0
      ? Math.round(
          sessions.reduce(
            (total, session) =>
              total +
              Number(
                session.score || 0
              ),
            0
          ) / totalSessions
        )
      : 0;

  const bestScore =
    totalSessions > 0
      ? Math.round(
          Math.max(
            ...sessions.map(
              (session) =>
                Number(
                  session.score || 0
                )
            )
          )
        )
      : 0;

  const uniquePoses =
    new Set(
      sessions
        .map(
          (session) =>
            session.pose
        )
        .filter(
          (pose) =>
            pose &&
            pose !== "Unknown" &&
            pose !== "string"
        )
    );

  const mudrasPracticed =
    uniquePoses.size;

  // ============================================================
  // STATUS CLASS
  // ============================================================

  const getStatusClass = (status) => {
    if (status === "Excellent") {
      return "excellent";
    }

    if (status === "Good") {
      return "good";
    }

    return "practice";
  };

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <div className="history-page">

      {/* ======================================================
          SHARED NAVIGATION
      ====================================================== */}

      <Navbar />

      {/* ======================================================
          MAIN
      ====================================================== */}

      <main>

        {/* ====================================================
            HERO
        ==================================================== */}

        <section className="history-hero">

          <span>
            PRACTICE HISTORY
          </span>

          <h1>
            Your Dance{" "}
            <strong>
              Progress
            </strong>
          </h1>

          <p>
            Review your previous practice
            sessions, recognition results,
            evaluation scores and improvement
            over time.
          </p>

        </section>

        {/* ====================================================
            SUMMARY
        ==================================================== */}

        <section className="history-summary">

          <div className="history-stat">

            <span>
              Practice Sessions
            </span>

            <strong>
              {loading
                ? "..."
                : totalSessions}
            </strong>

            <small>
              Total sessions
            </small>

          </div>

          <div className="history-stat">

            <span>
              Average Score
            </span>

            <strong>
              {loading
                ? "..."
                : `${averageScore}%`}
            </strong>

            <small>
              Across sessions
            </small>

          </div>

          <div className="history-stat">

            <span>
              Best Score
            </span>

            <strong>
              {loading
                ? "..."
                : `${bestScore}%`}
            </strong>

            <small>
              Highest evaluation
            </small>

          </div>

          <div className="history-stat">

            <span>
              Mudras Practiced
            </span>

            <strong>
              {loading
                ? "..."
                : mudrasPracticed}
            </strong>

            <small>
              Different classes
            </small>

          </div>

        </section>

        {/* ====================================================
            HISTORY
        ==================================================== */}

        <section className="history-section">

          <div className="history-section-heading">

            <div>

              <span>
                RECENT ACTIVITY
              </span>

              <h2>
                Practice Sessions
              </h2>

            </div>

            <Link
              to="/practice"
              className="history-practice-button"
            >
              Start Practice →
            </Link>

          </div>

          <div className="history-table">

            {/* TABLE HEADER */}

            <div className="history-table-header">

              <span>
                Date
              </span>

              <span>
                Detected Pose
              </span>

              <span>
                Confidence
              </span>

              <span>
                Score
              </span>

              <span>
                Status
              </span>

            </div>

            {/* LOADING */}

            {loading && (
              <div
                className="history-row"
                style={{
                  justifyContent:
                    "center",
                  padding: "30px",
                }}
              >
                <strong>
                  Loading practice history...
                </strong>
              </div>
            )}

            {/* ERROR */}

            {!loading &&
              error && (
                <div
                  className="history-row"
                  style={{
                    justifyContent:
                      "center",
                    padding: "30px",
                  }}
                >
                  <strong>
                    {error}
                  </strong>
                </div>
              )}

            {/* EMPTY */}

            {!loading &&
              !error &&
              sessions.length === 0 && (
                <div
                  className="history-row"
                  style={{
                    justifyContent:
                      "center",
                    padding: "40px",
                  }}
                >
                  <div
                    style={{
                      textAlign:
                        "center",
                      width: "100%",
                    }}
                  >
                    <strong>
                      No practice sessions yet.
                    </strong>

                    <small
                      style={{
                        display:
                          "block",
                        marginTop:
                          "8px",
                      }}
                    >
                      Start a practice
                      session to see
                      your results here.
                    </small>
                  </div>
                </div>
              )}

            {/* REAL MONGODB SESSIONS */}

            {!loading &&
              !error &&
              sessions.map(
                (session) => {
                  const formattedDate =
                    formatDate(
                      session.created_at
                    );

                  return (
                    <div
                      className="history-row"
                      key={session.id}
                    >

                      {/* DATE */}

                      <div>

                        <strong>
                          {
                            formattedDate.date
                          }
                        </strong>

                        <small>
                          {
                            formattedDate.time
                          }
                        </small>

                      </div>

                      {/* POSE */}

                      <div className="history-pose">

                        <span>
                          ✋
                        </span>

                        <strong>
                          {session.pose}
                        </strong>

                      </div>

                      {/* CONFIDENCE */}

                      <div>

                        <strong>
                          {Math.round(
                            Number(
                              session.confidence ||
                                0
                            )
                          )}
                          %
                        </strong>

                      </div>

                      {/* SCORE */}

                      <div className="history-score">

                        <strong>
                          {Math.round(
                            Number(
                              session.score ||
                                0
                            )
                          )}
                          %
                        </strong>

                      </div>

                      {/* STATUS */}

                      <div>

                        <span
                          className={`history-status ${getStatusClass(
                            session.status
                          )}`}
                        >
                          {
                            session.status
                          }
                        </span>

                      </div>

                    </div>
                  );
                }
              )}

          </div>

        </section>

        {/* ====================================================
            PROGRESS
        ==================================================== */}

        <section className="history-progress">

          <div className="history-progress-text">

            <span>
              YOUR PROGRESS
            </span>

            <h2>
              Keep practicing,
              <br />
              keep improving.
            </h2>

            <p>
              Consistent practice helps
              you improve your
              understanding of hand
              gestures, body alignment
              and classical dance
              postures.
            </p>

            <Link
              to="/practice"
              className="history-progress-button"
            >
              Practice Now
            </Link>

          </div>

          {/* PROGRESS CARD */}

          <div className="history-progress-card">

            <div className="progress-card-header">

              <div>

                <span>
                  Average Score
                </span>

                <strong>
                  {loading
                    ? "..."
                    : `${averageScore}%`}
                </strong>

              </div>

              <div className="progress-up">

                {totalSessions > 0
                  ? "✓ Tracking"
                  : "No sessions"}

              </div>

            </div>

            <div className="progress-bar">

              <div
                style={{
                  width: `${Math.min(
                    averageScore,
                    100
                  )}%`,
                }}
              ></div>

            </div>

            <p>
              Based on your recorded
              practice sessions
            </p>

          </div>

        </section>

      </main>

      {/* ======================================================
          FOOTER
      ====================================================== */}

      <footer className="history-footer">

        <div>

          <strong>
            Kuchipudi AI
          </strong>

          <p>
            Preserving classical dance
            through intelligent technology.
          </p>

        </div>

        <span>
          © 2026 Kuchipudi AI
        </span>

      </footer>

    </div>
  );
}

export default History;
