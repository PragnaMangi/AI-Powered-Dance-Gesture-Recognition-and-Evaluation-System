import React from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function Navbar() {
  const { user } = useAuth();

  const getNavClass = ({ isActive }) =>
    isActive ? "active" : "";

  return (
    <header className="navbar">

      {/* Logo */}
      <NavLink to="/" className="logo">
        <span className="logo-icon">✦</span>

        <div>
          <h2>Kuchipudi AI</h2>
          <span>Classical Dance Intelligence</span>
        </div>
      </NavLink>


      {/* Navigation */}
      <nav>

        <NavLink to="/" className={getNavClass}>
          Dashboard
        </NavLink>

        <NavLink to="/practice" className={getNavClass}>
          Practice
        </NavLink>

        <NavLink to="/mudras" className={getNavClass}>
          Mudras
        </NavLink>

        <NavLink to="/about" className={getNavClass}>
          About
        </NavLink>

        <NavLink to="/history" className={getNavClass}>
          History
        </NavLink>

      </nav>


      {/* User Profile Circle */}
      <NavLink
        to="/profile"
        className="profile-button"
        title={user?.name || "Profile"}
      >
        {user?.name?.trim()?.charAt(0)?.toUpperCase() || "?"}
      </NavLink>

    </header>
  );
}

export default Navbar;