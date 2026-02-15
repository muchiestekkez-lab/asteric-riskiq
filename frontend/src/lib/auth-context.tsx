'use client';

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { verifySession, login as apiLogin, logout as apiLogout, getToken, getHospital, clearToken } from './api';

interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  hospitalId: string | null;
  hospitalName: string | null;
}

interface AuthContextType extends AuthState {
  login: (accessCode: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    isAuthenticated: false,
    isLoading: true,
    hospitalId: null,
    hospitalName: null,
  });

  // Verify session on mount
  useEffect(() => {
    const token = getToken();
    if (!token) {
      setState({ isAuthenticated: false, isLoading: false, hospitalId: null, hospitalName: null });
      return;
    }

    verifySession().then((result) => {
      if (result?.valid) {
        setState({
          isAuthenticated: true,
          isLoading: false,
          hospitalId: result.hospital_id,
          hospitalName: result.hospital_name,
        });
      } else {
        clearToken();
        setState({ isAuthenticated: false, isLoading: false, hospitalId: null, hospitalName: null });
      }
    }).catch(() => {
      clearToken();
      setState({ isAuthenticated: false, isLoading: false, hospitalId: null, hospitalName: null });
    });
  }, []);

  const login = useCallback(async (accessCode: string) => {
    const data = await apiLogin(accessCode);
    setState({
      isAuthenticated: true,
      isLoading: false,
      hospitalId: data.hospital_id,
      hospitalName: data.hospital_name,
    });
  }, []);

  const logout = useCallback(async () => {
    await apiLogout();
    setState({ isAuthenticated: false, isLoading: false, hospitalId: null, hospitalName: null });
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
