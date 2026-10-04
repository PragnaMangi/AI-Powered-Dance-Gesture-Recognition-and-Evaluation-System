
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Navbar from "../components/Navbar";

const API_URL = "http://127.0.0.1:8000";

function Profile() {
  const {
    user,
    token,
    updateUser,
    logout,
  } = useAuth();

  const navigate = useNavigate();

  const [profile, setProfile] = useState({
    name: "",
    email: "",
    bio: "",
  });

  const [draftProfile, setDraftProfile] = useState({
    name: "",
    email: "",
    bio: "",
  });

  const [editing, setEditing] = useState(false);

  const [sessions, setSessions] = useState([]);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [loadingStats, setLoadingStats] = useState(true);

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saveMessage, setSaveMessage] = useState("");

  // ============================================================
  // LOAD CURRENT USER PROFILE
  // ============================================================

  useEffect(() => {
    if (token) {
      fetchProfile();
      fetchSessions();
    } else {
      setLoadingProfile(false);
      setLoadingStats(false);
    }
  }, [token]);

  // ============================================================
  // FETCH PROFILE
  // ============================================================

  const fetchProfile = async () => {
    try {
      setLoadingProfile(true);
      setError("");

      const response = await fetch(
        `${API_URL}/auth/me`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(
          "Unable to load your profile."
        );
      }

      const data = await response.json();

      const currentUser = data.user || {};

      const loadedProfile = {
        name: currentUser.name || "",
        email: currentUser.email || "",
        bio: currentUser.bio || "",
      };

      setProfile(loadedProfile);
      setDraftProfile(loadedProfile);

    } catch (err) {
      console.error(
        "Profile loading error:",
        err
      );

      setError(
        err.message ||
          "Unable to load your profile."
      );
    } finally {
      setLoadingProfile(false);
    }
  };

  // ============================================================
  // FETCH USER'S PRACTICE SESSIONS
  // ============================================================

  const fetchSessions = async () => {
    try {
      setLoadingStats(true);

      const response = await fetch(
        `${API_URL}/sessions`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(
          "Failed to fetch practice sessions."
        );
      }

      const data = await response.json();

      setSessions(
        data.sessions || []
      );

    } catch (err) {
      console.error(
        "Profile statistics error:",
        err
      );

      setSessions([]);

    } finally {
      setLoadingStats(false);
    }
  };

  // ============================================================
  // STATISTICS
  // ============================================================

  const totalSessions =
    sessions.length;

  const averageScore =
    totalSessions > 0
      ? Math.round(
          sessions.reduce(
            (
              total,
              session
            ) =>
              total +
              Number(
                session.score || 0
              ),
            0
          ) /
            totalSessions
        )
      : 0;

  const bestScore =
    totalSessions > 0
      ? Math.max(
          ...sessions.map(
            (session) =>
              Number(
                session.score || 0
              )
          )
        )
      : 0;

  const mudrasPracticed =
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
    ).size;

  // ============================================================
  // INPUT CHANGE
  // ============================================================

  const handleChange = (event) => {
    const {
      name,
      value,
    } = event.target;

    setDraftProfile(
      (previous) => ({
        ...previous,
        [name]: value,
      })
    );
  };

  // ============================================================
  // START EDITING
  // ============================================================

  const handleEdit = () => {
    setDraftProfile(profile);
    setSaveMessage("");
    setError("");
    setEditing(true);
  };

  // ============================================================
  // SAVE PROFILE TO MONGODB
  // ============================================================

  const handleSave = async () => {
    if (!draftProfile.name.trim()) {
      setError(
        "Name cannot be empty."
      );
      return;
    }

    try {
      setSaving(true);
      setError("");
      setSaveMessage("");

      const response = await fetch(
        `${API_URL}/profile`,
        {
          method: "PUT",

          headers: {
            "Content-Type":
              "application/json",

            Authorization:
              `Bearer ${token}`,
          },

          body: JSON.stringify({
            name:
              draftProfile.name.trim(),

            bio:
              draftProfile.bio.trim(),
          }),
        }
      );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Unable to update profile."
        );
      }

      const updatedUser =
        data.user || {
          ...user,
          name:
            draftProfile.name.trim(),
          bio:
            draftProfile.bio.trim(),
        };

      const updatedProfile = {
        name:
          updatedUser.name || "",
        email:
          updatedUser.email ||
          profile.email ||
          "",
        bio:
          updatedUser.bio || "",
      };

      setProfile(
        updatedProfile
      );

      setDraftProfile(
        updatedProfile
      );

      // Update AuthContext so the
      // navbar also shows the new
      // profile initial immediately.

      if (updateUser) {
        updateUser(
          updatedUser
        );
      }

      setEditing(false);

      setSaveMessage(
        "Profile updated successfully."
      );

    } catch (err) {
      console.error(
        "Profile update error:",
        err
      );

      setError(
        err.message ||
          "Unable to update profile."
      );

    } finally {
      setSaving(false);
    }
  };

  // ============================================================
  // CANCEL EDIT
  // ============================================================

  const handleCancel = () => {
    setDraftProfile(profile);
    setError("");
    setSaveMessage("");
    setEditing(false);
  };

  // ============================================================
  // LOGOUT
  // ============================================================

  const handleLogout = () => {
    logout();
    navigate("/login", {
      replace: true,
    });
  };

  // ============================================================
  // INITIALS
  // ============================================================

  const initials =
    profile.name
      ? profile.name
          .trim()
          .split(/\s+/)
          .map(
            (word) =>
              word.charAt(0)
          )
          .join("")
          .substring(0, 2)
          .toUpperCase()
      : "U";

  // ============================================================
  // LOADING
  // ============================================================

  if (
    loadingProfile &&
    !profile.name
  ) {
    return (
      <div className="auth-loading">
        <div className="auth-loading-spinner"></div>

        <p>
          Loading your profile...
        </p>
      </div>
    );
  }

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <div className="profile-page">

      {/* ======================================================
          SHARED NAVIGATION
      ====================================================== */}

      <Navbar />

      {/* ======================================================
          MAIN CONTENT
      ====================================================== */}

      <main className="profile-container">

        {/* ====================================================
            PAGE HEADING
        ==================================================== */}

        <div className="profile-page-heading">

          <div>

            <p className="profile-small-title">
              MY PROFILE
            </p>

            <h1>
              Welcome,{" "}
              {profile.name
                ? profile.name
                    .split(" ")[0]
                : "User"}{" "}
              👋
            </h1>

            <p>
              Manage your profile and
              view your dance practice
              progress.
            </p>

          </div>

          {!editing && (
            <button
              type="button"
              className="profile-edit-button"
              onClick={handleEdit}
            >
              ✏️ Edit Profile
            </button>
          )}

        </div>

        {/* ====================================================
            ERROR MESSAGE
        ==================================================== */}

        {error && (
          <div
            className="auth-error"
            style={{
              marginBottom:
                "20px",
            }}
          >
            {error}
          </div>
        )}

        {/* ====================================================
            SUCCESS MESSAGE
        ==================================================== */}

        {saveMessage && (
          <div
            style={{
              marginBottom:
                "20px",
              padding:
                "12px 16px",
              borderRadius:
                "10px",
              background:
                "#edf8ef",
              border:
                "1px solid #c8e6cc",
              color:
                "#26733a",
              fontSize:
                "14px",
            }}
          >
            {saveMessage}
          </div>
        )}

        {/* ====================================================
            PROFILE CARD
        ==================================================== */}

        <section className="profile-main-card">

          {/* PROFILE HEADER */}

          <div className="profile-avatar-section">

            <div className="profile-avatar">
              {initials}
            </div>

            <div>

              <h2>
                {profile.name ||
                  "User"}
              </h2>

              <p className="profile-course">
                {profile.email ||
                  "Email not available"}
              </p>

              <p className="profile-college">
                Kuchipudi AI
              </p>

            </div>

          </div>

          {/* ==================================================
              VIEW MODE
          ================================================== */}

          {!editing ? (
            <div className="profile-details">

              <div className="profile-detail-item">

                <span>
                  Name
                </span>

                <strong>
                  {profile.name ||
                    "Not provided"}
                </strong>

              </div>

              <div className="profile-detail-item">

                <span>
                  Email
                </span>

                <strong>
                  {profile.email ||
                    "Not provided"}
                </strong>

              </div>

              <div className="profile-detail-item profile-bio-item">

                <span>
                  About
                </span>

                <strong>
                  {profile.bio ||
                    "No bio added yet."}
                </strong>

              </div>

            </div>
          ) : (

            /* ==================================================
               EDIT MODE
            ================================================== */

            <div className="profile-edit-form">

              <div className="profile-form-group">

                <label>
                  Name
                </label>

                <input
                  type="text"
                  name="name"
                  value={
                    draftProfile.name
                  }
                  onChange={
                    handleChange
                  }
                  placeholder="Enter your name"
                />

              </div>

              <div className="profile-form-group">

                <label>
                  Email
                </label>

                <input
                  type="email"
                  value={
                    draftProfile.email
                  }
                  disabled
                />

                <small
                  style={{
                    color:
                      "#8a7a70",
                    marginTop:
                      "5px",
                    display:
                      "block",
                  }}
                >
                  Email cannot be changed here.
                </small>

              </div>

              <div className="profile-form-group">

                <label>
                  About
                </label>

                <textarea
                  name="bio"
                  value={
                    draftProfile.bio
                  }
                  onChange={
                    handleChange
                  }
                  rows="4"
                  placeholder="Tell us about yourself..."
                />

              </div>

              <div className="profile-form-actions">

                <button
                  type="button"
                  className="profile-cancel-button"
                  onClick={
                    handleCancel
                  }
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  type="button"
                  className="profile-save-button"
                  onClick={
                    handleSave
                  }
                  disabled={saving}
                >
                  {saving
                    ? "Saving..."
                    : "Save Profile"}
                </button>

              </div>

            </div>
          )}

        </section>

        {/* ====================================================
            STATISTICS
        ==================================================== */}

        <section className="profile-stats-section">

          <div className="profile-section-title">

            <div>

              <p className="profile-small-title">
                PRACTICE OVERVIEW
              </p>

              <h2>
                Your Dance Progress
              </h2>

            </div>

          </div>

          <div className="profile-stats-grid">

            {/* TOTAL SESSIONS */}

            <div className="profile-stat-card">

              <div className="profile-stat-icon">
                🎯
              </div>

              <div>

                <span>
                  Total Sessions
                </span>

                <strong>
                  {loadingStats
                    ? "..."
                    : totalSessions}
                </strong>

              </div>

            </div>

            {/* AVERAGE SCORE */}

            <div className="profile-stat-card">

              <div className="profile-stat-icon">
                ⭐
              </div>

              <div>

                <span>
                  Average Score
                </span>

                <strong>
                  {loadingStats
                    ? "..."
                    : `${averageScore}%`}
                </strong>

              </div>

            </div>

            {/* BEST SCORE */}

            <div className="profile-stat-card">

              <div className="profile-stat-icon">
                🏆
              </div>

              <div>

                <span>
                  Best Score
                </span>

                <strong>
                  {loadingStats
                    ? "..."
                    : `${bestScore}%`}
                </strong>

              </div>

            </div>

            {/* MUDRAS */}

            <div className="profile-stat-card">

              <div className="profile-stat-icon">
                🪷
              </div>

              <div>

                <span>
                  Mudras Practiced
                </span>

                <strong>
                  {loadingStats
                    ? "..."
                    : mudrasPracticed}
                </strong>

              </div>

            </div>

          </div>

        </section>

        {/* ====================================================
            QUICK ACTIONS
        ==================================================== */}

        <section className="profile-actions-section">

          <h2>
            Quick Actions
          </h2>

          <div className="profile-action-grid">

            <Link
              to="/practice"
              className="profile-action-card"
            >

              <span className="profile-action-icon">
                🎥
              </span>

              <div>

                <h3>
                  Start Practice
                </h3>

                <p>
                  Practice your mudras
                  and get AI feedback.
                </p>

              </div>

              <span className="profile-action-arrow">
                →
              </span>

            </Link>

            <Link
              to="/history"
              className="profile-action-card"
            >

              <span className="profile-action-icon">
                📊
              </span>

              <div>

                <h3>
                  View History
                </h3>

                <p>
                  Check your previous
                  practice sessions.
                </p>

              </div>

              <span className="profile-action-arrow">
                →
              </span>

            </Link>

            <Link
              to="/mudras"
              className="profile-action-card"
            >

              <span className="profile-action-icon">
                🖐️
              </span>

              <div>

                <h3>
                  Explore Mudras
                </h3>

                <p>
                  Learn about different
                  Kuchipudi mudras.
                </p>

              </div>

              <span className="profile-action-arrow">
                →
              </span>

            </Link>

          </div>

          {/* ==================================================
              LOGOUT
          ================================================== */}

          <div
            style={{
              marginTop: "28px",
              display: "flex",
              justifyContent: "center",
            }}
          >
            <button
              type="button"
              onClick={handleLogout}
              style={{
                padding: "12px 28px",
                borderRadius: "10px",
                border: "1px solid #e0c8ba",
                background: "#fff8f4",
                color: "#8b3f22",
                fontSize: "14px",
                fontWeight: "600",
                cursor: "pointer",
                transition:
                  "background 0.2s ease, transform 0.2s ease",
              }}
              onMouseEnter={(event) => {
                event.currentTarget.style.background =
                  "#f6e7de";
                event.currentTarget.style.transform =
                  "translateY(-1px)";
              }}
              onMouseLeave={(event) => {
                event.currentTarget.style.background =
                  "#fff8f4";
                event.currentTarget.style.transform =
                  "translateY(0)";
              }}
            >
              🚪 Logout
            </button>
          </div>

        </section>

      </main>

    </div>
  );
}

export default Profile;
