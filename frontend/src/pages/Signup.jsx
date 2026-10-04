
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Signup() {
  const navigate = useNavigate();
  const { signup } = useAuth();

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // --------------------------------------------------------
  // Handle input changes
  // --------------------------------------------------------

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));

    setError("");
  };

  // --------------------------------------------------------
  // Handle signup
  // --------------------------------------------------------

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");

    const name = formData.name.trim();
    const email = formData.email.trim();
    const password = formData.password;
    const confirmPassword =
      formData.confirmPassword;

    // ------------------------------------------------------
    // Validation
    // ------------------------------------------------------

    if (!name) {
      setError("Please enter your name.");
      return;
    }

    if (name.length < 2) {
      setError(
        "Name must contain at least 2 characters."
      );
      return;
    }

    if (!email) {
      setError("Please enter your email address.");
      return;
    }

    if (!password) {
      setError("Please enter a password.");
      return;
    }

    if (password.length < 6) {
      setError(
        "Password must contain at least 6 characters."
      );
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    // ------------------------------------------------------
    // Create account
    // ------------------------------------------------------

    setLoading(true);

    const result = await signup(
      name,
      email,
      password
    );

    setLoading(false);

    if (!result.success) {
      setError(
        result.message || "Could not create account."
      );
      return;
    }

    // Signup successful.
    // AuthContext automatically stores the token
    // and user information.

    navigate("/");
  };

  return (
    <div className="auth-page">

      <div className="auth-card">

        {/* ------------------------------------------------ */}
        {/* Header */}
        {/* ------------------------------------------------ */}

        <div className="auth-header">

          <span className="auth-logo">
            ✦
          </span>

          <h1>
            Create Account
          </h1>

          <p>
            Start your personalized
            Kuchipudi AI practice journey.
          </p>

        </div>

        {/* ------------------------------------------------ */}
        {/* Error */}
        {/* ------------------------------------------------ */}

        {error && (
          <div className="auth-error">
            {error}
          </div>
        )}

        {/* ------------------------------------------------ */}
        {/* Signup Form */}
        {/* ------------------------------------------------ */}

        <form
          className="auth-form"
          onSubmit={handleSubmit}
        >

          <div className="auth-field">

            <label htmlFor="name">
              Full Name
            </label>

            <input
              id="name"
              name="name"
              type="text"
              placeholder="Enter your name"
              value={formData.name}
              onChange={handleChange}
              autoComplete="name"
              disabled={loading}
            />

          </div>

          <div className="auth-field">

            <label htmlFor="email">
              Email
            </label>

            <input
              id="email"
              name="email"
              type="email"
              placeholder="Enter your email"
              value={formData.email}
              onChange={handleChange}
              autoComplete="email"
              disabled={loading}
            />

          </div>

          <div className="auth-field">

            <label htmlFor="password">
              Password
            </label>

            <input
              id="password"
              name="password"
              type="password"
              placeholder="Create a password"
              value={formData.password}
              onChange={handleChange}
              autoComplete="new-password"
              disabled={loading}
            />

          </div>

          <div className="auth-field">

            <label htmlFor="confirmPassword">
              Confirm Password
            </label>

            <input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              placeholder="Confirm your password"
              value={formData.confirmPassword}
              onChange={handleChange}
              autoComplete="new-password"
              disabled={loading}
            />

          </div>

          <button
            type="submit"
            className="auth-submit-button"
            disabled={loading}
          >

            {loading
              ? "Creating Account..."
              : "Create Account"}

          </button>

        </form>

        {/* ------------------------------------------------ */}
        {/* Login Link */}
        {/* ------------------------------------------------ */}

        <div className="auth-footer">

          <span>
            Already have an account?
          </span>

          <Link to="/login">
            Sign In
          </Link>

        </div>

      </div>

    </div>
  );
}
