"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { auth } from "./api";

type AuthState = {
  token: string | null;
  email: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [email, setEmail] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("token");
    if (stored) {
      setToken(stored);
      auth.me().then((u) => setEmail(u.email)).catch(() => logout());
    }
    setLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    const res = await auth.login(email, password);
    localStorage.setItem("token", res.access_token);
    setToken(res.access_token);
    const me = await auth.me();
    setEmail(me.email);
  };

  const register = async (email: string, password: string) => {
    const res = await auth.register(email, password);
    localStorage.setItem("token", res.access_token);
    setToken(res.access_token);
    setEmail(email);
  };

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setEmail(null);
  };

  return (
    <AuthContext.Provider value={{ token, email, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
