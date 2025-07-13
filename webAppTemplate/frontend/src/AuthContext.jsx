import React, { createContext, useContext, useState } from 'react';
import axios from 'axios';
const API_URL = '/api'; // Use relative path for Nginx proxy

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('jwt') || null);
  const [user, setUser] = useState(() => localStorage.getItem('user') || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const login = async (username, password) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await axios.post(`${API_URL}/login`, new URLSearchParams({ username, password }));
      setToken(resp.data.access_token);
      setUser(username);
      localStorage.setItem('jwt', resp.data.access_token);
      localStorage.setItem('user', username);
      setLoading(false);
      return true;
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
      setLoading(false);
      return false;
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('jwt');
    localStorage.removeItem('user');
  };

  const isAuthenticated = !!token;

  return (
    <AuthContext.Provider value={{ token, user, isAuthenticated, login, logout, loading, error }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
} 