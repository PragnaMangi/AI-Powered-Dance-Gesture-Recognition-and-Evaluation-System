import {
  BrowserRouter,
  Routes,
  Route,
  Link,
  Navigate,
} from "react-router-dom";

import "./index.css";

import PracticePage from "./pages/Practice";
import Mudras from "./pages/Mudras";
import About from "./pages/About";
import History from "./pages/History";
import Profile from "./pages/Profile";

import Login from "./pages/Login";
import Signup from "./pages/Signup";

import Navbar from "./components/Navbar";

import {
  AuthProvider,
  useAuth,
} from "./context/AuthContext";


function ProtectedRoute({ children }) {
  const {
    user,
    loading,
  } = useAuth();

  if (loading) {
    return (
      <div className="auth-loading">
        <div className="auth-loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  if (!user) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }

  return children;
}


function Dashboard() {
  return (
    <div className="app">

      <Navbar />


      <main className="dashboard">

        {/* HERO */}

        <section className="hero">

          <div>

            <p className="eyebrow">
              KUCHIPUDI DANCE • AI ASSISTANT
            </p>


            <h1>

              Perfect your

              <br />

              <span>
                Dance
              </span>{" "}
              with AI

            </h1>


            <p className="hero-text">

              Practice classical dance mudras and postures with
              real-time AI recognition, accuracy analysis, and
              personalized feedback.

            </p>


            <Link
              to="/practice"
              className="primary-button"
            >
              Start Practice →
            </Link>

          </div>


          <div className="hero-art">

            <div className="dance-circle">

              <a
                href="https://in.pinterest.com/pin/307089268364823379/"
                target="_blank"
                rel="noopener noreferrer"
              >

                <img
                  src="/dance-image.jpg"
                  alt="Classical dance pose"
                />

              </a>

            </div>

          </div>

        </section>


        {/* STATS */}

        <section className="stats">

          <div className="stat-card">

            <span>
              🎯
            </span>

            <div>

              <strong>
                AI Recognition
              </strong>

              <p>
                Real-time pose analysis
              </p>

            </div>

          </div>


          <div className="stat-card">

            <span>
              🖐️
            </span>

            <div>

              <strong>
                Mudra Analysis
              </strong>

              <p>
                Hand gesture recognition
              </p>

            </div>

          </div>


          <div className="stat-card">

            <span>
              📈
            </span>

            <div>

              <strong>
                Progress Tracking
              </strong>

              <p>
                Monitor your improvement
              </p>

            </div>

          </div>

        </section>


        {/* FEATURES */}

        <section className="section">

          <div className="section-heading">

            <div>

              <p className="eyebrow">
                EXPLORE
              </p>

              <h2>
                Continue your practice
              </h2>

            </div>

          </div>


          <div className="feature-grid">


            <Link
              to="/practice"
              className="feature-card"
            >

              <div className="feature-icon">
                📷
              </div>

              <h3>
                Live Practice
              </h3>

              <p>
                Open your camera and get instant AI feedback on
                your dance pose.
              </p>

              <span>
                Practice now →
              </span>

            </Link>


            <Link
              to="/mudras"
              className="feature-card"
            >

              <div className="feature-icon">
                🪷
              </div>

              <h3>
                Learn Mudras
              </h3>

              <p>
                Explore classical mudras and understand their
                correct hand positions.
              </p>

              <span>
                Explore mudras →
              </span>

            </Link>


            <Link
              to="/history"
              className="feature-card"
            >

              <div className="feature-icon">
                📊
              </div>

              <h3>
                Your Progress
              </h3>

              <p>
                Review previous practice sessions and track your
                recognition accuracy.
              </p>

              <span>
                View progress →
              </span>

            </Link>


          </div>

        </section>


      </main>

    </div>
  );
}


function App() {

  return (

    <BrowserRouter>

      <AuthProvider>

        <Routes>

          {/* AUTH ROUTES */}

          <Route
            path="/login"
            element={<Login />}
          />

          <Route
            path="/signup"
            element={<Signup />}
          />


          {/* DASHBOARD */}

          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />


          {/* PRACTICE */}

          <Route
            path="/practice"
            element={
              <ProtectedRoute>
                <PracticePage />
              </ProtectedRoute>
            }
          />


          {/* MUDRAS */}

          <Route
            path="/mudras"
            element={
              <ProtectedRoute>
                <Mudras />
              </ProtectedRoute>
            }
          />


          {/* ABOUT */}

          <Route
            path="/about"
            element={
              <ProtectedRoute>
                <About />
              </ProtectedRoute>
            }
          />


          {/* HISTORY */}

          <Route
            path="/history"
            element={
              <ProtectedRoute>
                <History />
              </ProtectedRoute>
            }
          />


          {/* PROFILE */}

          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            }
          />


          {/* UNKNOWN ROUTES */}

          <Route
            path="*"
            element={
              <Navigate
                to="/"
                replace
              />
            }
          />

        </Routes>

      </AuthProvider>

    </BrowserRouter>

  );
}

export default App;