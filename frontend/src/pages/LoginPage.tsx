import { useState } from 'react';

import { apiPost } from '../api/client';
import type { AuthMessage, AuthUser } from '../types';

const normalizeEmail = (value: string): string => value.trim().toLowerCase();

const isValidEmail = (value: string): boolean => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());

interface LoginPageProps {
  onLogin: (user: AuthUser) => void;
  onBackHome: () => void;
}

export function LoginPage({ onLogin, onBackHome }: LoginPageProps) {
  const [mode, setMode] = useState<'login' | 'signup' | 'forgot'>('login');

  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [notification, setNotification] = useState('');

  const clearAuthFields = (clearNotification = true) => {
    setError('');
    setPassword('');
    setEmail('');
    if (clearNotification) setNotification('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (mode !== 'login') setNotification('');

    if (!username.trim()) {
      setError('Username is required');
      return;
    }

    try {
      if (mode === 'login') {
        const loggedInUser = await apiPost<AuthUser>('/auth/login', { username, password });
        onLogin(loggedInUser);
        return;
      }

      if (!email.trim()) {
        setError('Email is required');
        return;
      }
      if (!isValidEmail(email)) {
        setError('Please enter a valid email address');
        return;
      }
      if (!password.trim()) {
        setError(mode === 'forgot' ? 'New password is required' : 'Password is required');
        return;
      }

      const normalizedEmail = normalizeEmail(email);
      if (mode === 'signup') {
        await apiPost<AuthUser>('/auth/signup', {
          username,
          email: normalizedEmail,
          password,
        });
        setNotification('Account created successfully. You can now log in.');
        setMode('login');
        clearAuthFields(false);
        return;
      }

      const response = await apiPost<AuthMessage>('/auth/reset-password', {
        username,
        email: normalizedEmail,
        new_password: password,
      });
      setNotification(response.message || 'Password reset successful. You can now log in.');
      setMode('login');
      clearAuthFields(false);
    } catch (err) {
      setError(String(err));
    }
  };

  return (
    <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f4f7fb', fontFamily: 'Arial, sans-serif' }}>
      <form onSubmit={handleSubmit} style={{ background: 'white', padding: 32, borderRadius: 8, boxShadow: '0 4px 12px rgba(0,0,0,0.1)', display: 'grid', gap: 16, width: 300 }}>
        <h2 style={{ margin: 0, textAlign: 'center' }}>
          {mode === 'login' && 'Login'}
          {mode === 'signup' && 'Create Account'}
          {mode === 'forgot' && 'Reset Password'}
        </h2>
        {error && <div style={{ color: 'red', fontSize: 14 }}>{error}</div>}
        {notification && <div style={{ color: 'green', fontSize: 14 }}>{notification}</div>}

        <input
          placeholder="Username"
          value={username}
          onChange={e => setUsername(e.target.value)}
          style={{ padding: 8, border: '1px solid #ccc', borderRadius: 4 }}
        />

        {(mode === 'signup' || mode === 'forgot') && (
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            style={{ padding: 8, border: '1px solid #ccc', borderRadius: 4 }}
          />
        )}

        <input
          type="password"
          placeholder={mode === 'forgot' ? 'New Password' : 'Password'}
          value={password}
          onChange={e => setPassword(e.target.value)}
          style={{ padding: 8, border: '1px solid #ccc', borderRadius: 4 }}
        />

        <button type="submit" style={{ padding: 10, background: '#0066cc', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer' }}>
          {mode === 'login' && 'Login'}
          {mode === 'signup' && 'Sign Up'}
          {mode === 'forgot' && 'Reset'}
        </button>

        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginTop: 8 }}>
          {mode !== 'login' ? (
            <span style={{ color: '#0066cc', cursor: 'pointer' }} onClick={() => { setMode('login'); clearAuthFields(); }}>Back to Login</span>
          ) : (
            <>
              <span style={{ color: '#0066cc', cursor: 'pointer' }} onClick={() => { setMode('signup'); clearAuthFields(); }}>Create Account</span>
              <span style={{ color: '#0066cc', cursor: 'pointer' }} onClick={() => { setMode('forgot'); clearAuthFields(); }}>Forgot Password?</span>
            </>
          )}
        </div>
        <div style={{ textAlign: 'center', fontSize: 13 }}>
          <button
            type="button"
            onClick={() => onBackHome()}
            style={{ background: 'none', border: 'none', color: '#0066cc', cursor: 'pointer', padding: 0 }}
          >
            Back to Home
          </button>
        </div>
      </form>
    </div>
  );
}

