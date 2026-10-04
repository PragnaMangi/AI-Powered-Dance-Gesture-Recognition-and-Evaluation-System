
// ============================================================
// frontend/src/pages/About.jsx
// ============================================================

import React from "react";
import { Link } from "react-router-dom";
import Navbar from "../components/Navbar";

function About() {
  return (
    <div className="about-page">
      {/* Common Navigation */}
      <Navbar />

      {/* Hero Section */}
      <section className="about-hero">
        <p className="about-eyebrow">
          ABOUT THE PROJECT
        </p>

        <h1>
          Technology meets
          <span> Tradition</span>
        </h1>

        <p>
          Kuchipudi AI is an AI-powered classical dance recognition
          and evaluation system designed to help dancers practice
          mudras and dance postures with real-time feedback.
        </p>
      </section>

      {/* Introduction */}
      <section className="about-introduction">
        <div className="about-intro-text">
          <p className="about-eyebrow">
            OUR VISION
          </p>

          <h2>
            Making classical dance
            <br />
            practice more intelligent.
          </h2>

          <p>
            Classical Indian dance requires precise hand gestures,
            body alignment, posture, and movement. Traditionally,
            learners depend heavily on instructors to identify
            mistakes and improve their technique.
          </p>

          <p>
            Kuchipudi AI combines computer vision and machine
            learning to provide an additional digital practice
            assistant. The system analyzes the dancer through a
            camera and recognizes trained mudras and postures.
          </p>

          <Link
            to="/practice"
            className="about-primary-button"
          >
            Start Practicing →
          </Link>
        </div>

        <div className="about-visual">
          <div className="about-visual-circle">
            <img
              src="/ai.jpg"
              alt="AI + Dance"
            />
          </div>

          <div className="about-visual-card">
            <strong>AI + Dance</strong>

            <span>
              Tradition powered by technology
            </span>
          </div>
        </div>
      </section>

      {/* What the System Does */}
      <section className="about-section">
        <div className="about-section-heading">
          <p className="about-eyebrow">
            WHAT IT DOES
          </p>

          <h2>
            An intelligent dance
            <br />
            practice assistant
          </h2>
        </div>

        <div className="about-feature-grid">
          <article className="about-feature-card">
            <div className="about-feature-icon">
              📷
            </div>

            <h3>Real-Time Recognition</h3>

            <p>
              Uses the camera to analyze the dancer and identify
              trained classical dance mudras and postures.
            </p>
          </article>

          <article className="about-feature-card">
            <div className="about-feature-icon">
              🖐️
            </div>

            <h3>Mudra Analysis</h3>

            <p>
              Examines hand landmarks and gesture characteristics
              to recognize different classical hand gestures.
            </p>
          </article>

          <article className="about-feature-card">
            <div className="about-feature-icon">
              🎯
            </div>

            <h3>Pose Evaluation</h3>

            <p>
              Compares detected dance posture characteristics with
              learned reference patterns.
            </p>
          </article>

          <article className="about-feature-card">
            <div className="about-feature-icon">
              💬
            </div>

            <h3>AI Feedback</h3>

            <p>
              Provides understandable feedback to help dancers
              identify areas that need improvement.
            </p>
          </article>
        </div>
      </section>

      {/* Call To Action */}
      <section className="about-cta">
        <div>
          <p className="about-eyebrow">
            READY TO BEGIN?
          </p>

          <h2>
            Practice your
            <br />
            <span>dance with AI.</span>
          </h2>

          <p>
            Open the camera and explore real-time classical dance
            recognition and feedback.
          </p>
        </div>

        <Link
          to="/practice"
          className="about-cta-button"
        >
          Start Practice →
        </Link>
      </section>

      {/* Footer */}
      <footer className="about-footer">
        <span>© 2026 Kuchipudi AI</span>

        <span>
          AI-Powered Classical Dance Recognition
        </span>
      </footer>
    </div>
  );
}

export default About;
