
import React from "react";
import { Link } from "react-router-dom";
import Navbar from "../components/Navbar";

const mudras = [
  {
    name: "Alapadma",
    description:
      "A graceful open-palm gesture representing a fully bloomed lotus.",
    image: "/mudras/alapadma.jpg",
  },
  {
    name: "Anjali",
    description:
      "A gesture formed by joining both palms, commonly expressing respect and greeting.",
    image: "/mudras/anjali.jpg",
  },
  {
    name: "Brahma",
    description:
      "A classical hand gesture associated with Brahma and symbolic expression.",
    image: "/mudras/brahma.jpg",
  },
  {
    name: "Matsya",
    description:
      "A hand gesture representing a fish in classical Indian dance.",
    image: "/mudras/matsya.jpg",
  },
  {
    name: "Mushti",
    description:
      "A closed-fist gesture used to express strength and various dance meanings.",
    image: "/mudras/mushti.jpg",
  },
  {
    name: "Nataraja",
    description:
      "A gesture associated with Lord Nataraja and the cosmic dance.",
    image: "/mudras/nataraja.jpg",
  },
  {
    name: "Parvathi",
    description:
      "A graceful gesture associated with Goddess Parvathi.",
    image: "/mudras/parvathi.jpg",
  },
  {
    name: "Pataka",
    description:
      "A flat-hand gesture frequently used in classical Indian dance.",
    image: "/mudras/pataka.jpg",
  },
  {
    name: "Saraswathi",
    description:
      "A gesture associated with Goddess Saraswathi and artistic expression.",
    image: "/mudras/saraswathi.jpg",
  },
  {
    name: "Shivalinga",
    description:
      "A symbolic gesture representing Lord Shiva.",
    image: "/mudras/shivalinga.jpg",
  },
];

function Mudras() {
  return (
    <div className="mudras-page">
      {/* Shared Navigation */}
      <Navbar />

      {/* Hero Section */}
      <section className="mudras-hero">
        <p className="mudras-eyebrow">
          CLASSICAL DANCE • MUDRA LIBRARY
        </p>

        <h1>
          Explore the <span>Mudras</span>
        </h1>

        <p>
          Discover the classical hand gestures recognized by
          our AI-powered dance analysis system.
        </p>
      </section>

      {/* Mudra Cards */}
      <main className="mudras-section">
        <div className="mudras-grid">
          {mudras.map((mudra, index) => (
            <article
              className="mudra-card"
              key={mudra.name}
            >
              <div className="mudra-image-container">
                <img
                  src={mudra.image}
                  alt={`${mudra.name} mudra`}
                  onError={(event) => {
                    event.currentTarget.style.display = "none";

                    event.currentTarget.parentElement.classList.add(
                      "image-placeholder"
                    );
                  }}
                />

                <span className="mudra-number">
                  {String(index + 1).padStart(2, "0")}
                </span>
              </div>

              <div className="mudra-content">
                <h2>{mudra.name}</h2>

                <p>{mudra.description}</p>

                <Link
                  to="/practice"
                  className="practice-mudra-button"
                >
                  Practice this mudra →
                </Link>
              </div>
            </article>
          ))}
        </div>
      </main>

      {/* Call To Action */}
      <section className="mudras-cta">
        <div>
          <p className="mudras-eyebrow">
            READY TO PRACTICE?
          </p>

          <h2>
            Put your mudra
            <br />
            <span>to the test.</span>
          </h2>

          <p>
            Stand in front of your camera and let our AI
            analyze your dance pose and hand gesture.
          </p>
        </div>

        <Link
          to="/practice"
          className="mudras-cta-button"
        >
          Start Practicing →
        </Link>
      </section>

      {/* Footer */}
      <footer className="mudras-footer">
        <span>© 2026 Kuchipudi AI</span>

        <span>
          AI-Powered Classical Dance Recognition
        </span>
      </footer>
    </div>
  );
}

export default Mudras;
