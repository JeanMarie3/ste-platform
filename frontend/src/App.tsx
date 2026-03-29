import { Dashboard } from './pages/Dashboard';
import { useEffect, useState } from 'react';

import { apiGet, apiPost } from './api/client';
import type { AuthMessage, AuthUser } from './types';

const normalizeEmail = (value: string): string => value.trim().toLowerCase();

const isValidEmail = (value: string): boolean => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());

type SessionUser = { username: string; email: string; role: 'admin' | 'standard' };

export default function App() {
  const [user, setUser] = useState<SessionUser | null>(() => {
    const savedSession = sessionStorage.getItem('ste.currentUser');
    if (savedSession) {
      const parsed = JSON.parse(savedSession) as Partial<SessionUser>;
      if (parsed.username && parsed.role) {
        return { username: parsed.username, role: parsed.role, email: parsed.email ?? '' };
      }
    }
    return null;
  });

  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteEmail, setDeleteEmail] = useState('');
  const [deletePassword, setDeletePassword] = useState('');
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [deleteBusy, setDeleteBusy] = useState(false);
  const [deleteError, setDeleteError] = useState('');

  useEffect(() => {
    if (!user) return;

    let cancelled = false;

    const validateSessionUser = async () => {
      try {
        const users = await apiGet<AuthUser[]>('/auth/users');
        const stillExists = users.some(
          (item) => item.username === user.username && item.role === user.role && item.email === user.email,
        );
        if (!stillExists && !cancelled) {
          sessionStorage.removeItem('ste.currentUser');
          setUser(null);
          setDeleteOpen(false);
          setDeleteError('');
          setDeletePassword('');
          setDeleteConfirmText('');
          setDeleteEmail('');
        }
      } catch {
        // Keep the current session if auth API is temporarily unreachable.
      }
    };

    validateSessionUser();

    return () => {
      cancelled = true;
    };
  }, [user]);

  const handleLogin = (loggedInUser: AuthUser) => {
    setUser(loggedInUser);
    sessionStorage.setItem('ste.currentUser', JSON.stringify(loggedInUser));
    setDeleteOpen(false);
    setDeleteError('');
    setDeletePassword('');
    setDeleteConfirmText('');
    setDeleteEmail(loggedInUser.email);
  };

  const handleLogout = () => {
    setUser(null);
    sessionStorage.removeItem('ste.currentUser');
    setDeleteOpen(false);
    setDeleteError('');
    setDeletePassword('');
    setDeleteConfirmText('');
    setDeleteEmail('');
  };

  const handleDeleteAccount = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!user) return;
    setDeleteError('');

    if (!deleteEmail.trim()) {
      setDeleteError('Email is required');
      return;
    }
    if (!isValidEmail(deleteEmail)) {
      setDeleteError('Please enter a valid email address');
      return;
    }
    if (!deletePassword.trim()) {
      setDeleteError('Password is required');
      return;
    }
    if (deleteConfirmText.trim().toUpperCase() !== 'DELETE') {
      setDeleteError('Type DELETE to confirm account deletion');
      return;
    }

    setDeleteBusy(true);
    try {
      const response = await apiPost<AuthMessage>('/auth/delete-account', {
        username: user.username,
        email: normalizeEmail(deleteEmail),
        password: deletePassword,
        confirmation_text: deleteConfirmText,
      });
      window.alert(response.message || 'Account deleted successfully');
      handleLogout();
    } catch (err) {
      setDeleteError(String(err));
    } finally {
      setDeleteBusy(false);
    }
  };

  if (!user) {
    return <AuthScreen onLogin={handleLogin} />;
  }

  return (
    <main style={{ minHeight: '100vh', background: '#f4f7fb', color: '#17212b', padding: 24, fontFamily: 'Arial, sans-serif' }}>
      <header style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ marginBottom: 8 }}>Software Testing Engine</h1>
          <p style={{ margin: 0 }}>Web control plane starter for requirements, generated test cases, and executions.</p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div>Logged in as <strong>{user.username}</strong> ({user.role})</div>
          <div style={{ fontSize: 12, color: '#6f7c8a' }}>{user.email}</div>
          <button style={{ marginTop: 8 }} onClick={handleLogout}>Logout</button>
          <div>
            <button
              style={{ marginTop: 8, background: '#b42318', color: '#fff', border: 'none', borderRadius: 4, padding: '6px 10px', cursor: 'pointer' }}
              onClick={() => {
                setDeleteOpen((current) => !current);
                setDeleteError('');
                setDeletePassword('');
                setDeleteConfirmText('');
                setDeleteEmail(user.email);
              }}
            >
              {deleteOpen ? 'Cancel delete' : 'Delete my account'}
            </button>
          </div>
        </div>
      </header>
      {deleteOpen && (
        <form onSubmit={handleDeleteAccount} style={{ marginBottom: 16, maxWidth: 460, background: '#fff1f0', border: '1px solid #f5c2c7', borderRadius: 8, padding: 12, display: 'grid', gap: 8 }}>
          <strong style={{ color: '#7a1f1f' }}>Danger zone: Delete account</strong>
          <div style={{ fontSize: 12, color: '#7a1f1f' }}>This action is permanent. Enter your credentials and type DELETE to confirm.</div>
          {deleteError && <div style={{ color: '#b42318', fontSize: 13 }}>{deleteError}</div>}
          <input
            type="email"
            placeholder="Your account email"
            value={deleteEmail}
            onChange={(e) => setDeleteEmail(e.target.value)}
            style={{ padding: 8, border: '1px solid #d0d7de', borderRadius: 4 }}
          />
          <input
            type="password"
            placeholder="Current password"
            value={deletePassword}
            onChange={(e) => setDeletePassword(e.target.value)}
            style={{ padding: 8, border: '1px solid #d0d7de', borderRadius: 4 }}
          />
          <input
            placeholder="Type DELETE"
            value={deleteConfirmText}
            onChange={(e) => setDeleteConfirmText(e.target.value)}
            style={{ padding: 8, border: '1px solid #d0d7de', borderRadius: 4 }}
          />
          <button type="submit" disabled={deleteBusy} style={{ width: 'fit-content', background: '#b42318', color: '#fff', border: 'none', borderRadius: 4, padding: '8px 12px', cursor: 'pointer' }}>
            {deleteBusy ? 'Deleting...' : 'Permanently delete account'}
          </button>
        </form>
      )}
      <Dashboard userRole={user.role} />
    </main>
  );
}

function AuthScreen({ onLogin }: {
  onLogin: (user: AuthUser) => void;
}) {
  const [mode, setMode] = useState<'login' | 'signup' | 'forgot'>('login');

  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'admin' | 'standard'>('standard');
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
          role,
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

        {mode === 'signup' && (
          <select
            value={role}
            onChange={e => setRole(e.target.value as 'admin' | 'standard')}
            style={{ padding: 8, border: '1px solid #ccc', borderRadius: 4 }}
          >
            <option value="standard">Standard User</option>
            <option value="admin">Admin User</option>
          </select>
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
      </form>
    </div>
  );
}
