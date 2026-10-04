
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
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
  // Handle login
  // --------------------------------------------------------

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");

    const email = formData.email.trim();
    const password = formData.password;

    if (!email) {
      setError("Please enter your email address.");
      return;
    }

    if (!password) {
      setError("Please enter your password.");
      return;
    }

    setLoading(true);

    const result = await login(
      email,
      password
    );

    setLoading(false);

    if (!result.success) {
      setError(
        result.message || "Login failed."
      );
      return;
    }

    // Login successful
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
            Welcome
          </h1>

          <p>
            Sign in to continue your
            Kuchipudi AI practice.
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
        {/* Login Form */}
        {/* ------------------------------------------------ */}

        <form
          className="auth-form"
          onSubmit={handleSubmit}
        >

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
              placeholder="Enter your password"
              value={formData.password}
              onChange={handleChange}
              autoComplete="current-password"
              disabled={loading}
            />

          </div>

          <button
            type="submit"
            className="auth-submit-button"
            disabled={loading}
          >

            {loading
              ? "Signing in..."
              : "Sign In"}

          </button>

        </form>

        {/* ------------------------------------------------ */}
        {/* Signup Link */}
        {/* ------------------------------------------------ */}

        <div className="auth-footer">

          <span>
            Don't have an account?
          </span>

          <Link to="/signup">
            Create Account
          </Link>

        </div>

      </div>

    </div>
  );
}
