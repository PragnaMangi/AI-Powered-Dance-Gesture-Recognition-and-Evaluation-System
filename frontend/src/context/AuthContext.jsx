
import {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

const AuthContext = createContext(null);

const API_URL = "http://127.0.0.1:8000";

export function AuthProvider({ children }) {
  // ============================================================
  // AUTH STATE
  // ============================================================

  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);

  // Used while restoring the login session after refresh
  const [loading, setLoading] = useState(true);

  // ============================================================
  // RESTORE LOGIN SESSION AFTER PAGE REFRESH
  // ============================================================

  useEffect(() => {
    const restoreSession = () => {
      try {
        const savedToken =
          sessionStorage.getItem(
            "dance_ai_token"
          );

        const savedUser =
          sessionStorage.getItem(
            "dance_ai_user"
          );

        if (savedToken && savedUser) {
          const parsedUser =
            JSON.parse(savedUser);

          setToken(savedToken);
          setUser(parsedUser);

          console.log(
            "✅ Login session restored after refresh."
          );
        } else {
          setToken(null);
          setUser(null);

          console.log(
            "ℹ️ No saved login session found."
          );
        }
      } catch (error) {
        console.error(
          "❌ Failed to restore login session:",
          error
        );

        sessionStorage.removeItem(
          "dance_ai_token"
        );

        sessionStorage.removeItem(
          "dance_ai_user"
        );

        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    restoreSession();
  }, []);

  // ============================================================
  // LOGIN
  // ============================================================

  const login = async (email, password) => {
    try {
      const formData =
        new URLSearchParams();

      formData.append(
        "username",
        email
      );

      formData.append(
        "password",
        password
      );

      const response =
        await fetch(
          `${API_URL}/auth/login`,
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/x-www-form-urlencoded",
            },

            body: formData.toString(),
          }
        );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Login failed."
        );
      }

      const accessToken =
        data.access_token ||
        data.token;

      if (!accessToken) {
        throw new Error(
          "Login succeeded but no authentication token was returned."
        );
      }

      // Save login session
      sessionStorage.setItem(
        "dance_ai_token",
        accessToken
      );

      if (data.user) {
        sessionStorage.setItem(
          "dance_ai_user",
          JSON.stringify(data.user)
        );
      }

      // Update React state
      setToken(accessToken);
      setUser(data.user || null);

      return {
        success: true,
        user: data.user,
      };
    } catch (error) {
      console.error(
        "Login error:",
        error
      );

      return {
        success: false,
        message:
          error.message ||
          "Login failed.",
      };
    }
  };

  // ============================================================
  // SIGNUP
  // ============================================================

  const signup = async (
    name,
    email,
    password
  ) => {
    try {
      const response =
        await fetch(
          `${API_URL}/auth/signup`,
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body: JSON.stringify({
              name,
              email,
              password,
            }),
          }
        );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Signup failed."
        );
      }

      const accessToken =
        data.access_token ||
        data.token;

      // If signup automatically logs
      // the user in, save the session.
      if (accessToken) {
        sessionStorage.setItem(
          "dance_ai_token",
          accessToken
        );

        if (data.user) {
          sessionStorage.setItem(
            "dance_ai_user",
            JSON.stringify(data.user)
          );
        }

        setToken(accessToken);
        setUser(data.user || null);
      }

      return {
        success: true,
        user: data.user,
      };
    } catch (error) {
      console.error(
        "Signup error:",
        error
      );

      return {
        success: false,
        message:
          error.message ||
          "Signup failed.",
      };
    }
  };

  // ============================================================
  // LOGOUT
  // ============================================================

  const logout = () => {
    // Remove current session
    sessionStorage.removeItem(
      "dance_ai_token"
    );

    sessionStorage.removeItem(
      "dance_ai_user"
    );

    // Also remove any old localStorage
    // values from previous versions.
    localStorage.removeItem(
      "dance_ai_token"
    );

    localStorage.removeItem(
      "dance_ai_user"
    );

    setToken(null);
    setUser(null);

    console.log(
      "👋 User logged out."
    );
  };

  // ============================================================
  // UPDATE USER
  // ============================================================

  const updateUser = (
    updatedUser
  ) => {
    setUser(updatedUser);

    if (updatedUser) {
      sessionStorage.setItem(
        "dance_ai_user",
        JSON.stringify(updatedUser)
      );
    }
  };

  // ============================================================
  // AUTH CONTEXT
  // ============================================================

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,

        login,
        signup,
        logout,
        updateUser,

        isAuthenticated:
          !!token && !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// ============================================================
// USE AUTH HOOK
// ============================================================

export function useAuth() {
  return useContext(
    AuthContext
  );
}
