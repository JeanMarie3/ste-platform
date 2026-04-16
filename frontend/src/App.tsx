import { Dashboard } from './pages/Dashboard';
import { useEffect, useMemo, useRef, useState } from 'react';
import { HomePage } from './pages/HomePage';
import { LoginPage } from './pages/LoginPage';

import { apiGet, apiPost } from './api/client';
import type { AuthMessage, AuthUser } from './types';

const normalizeEmail = (value: string): string => value.trim().toLowerCase();

const isValidEmail = (value: string): boolean => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());

type SessionUser = { username: string; email: string; role: 'admin' | 'standard' };

const getHashRoute = (): string => {
  return window.location.hash.slice(1) || 'home';
};

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
  const [currentRoute, setCurrentRoute] = useState<string>(getHashRoute());
  const [deleteEmail, setDeleteEmail] = useState('');
  const [deletePassword, setDeletePassword] = useState('');
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [deleteBusy, setDeleteBusy] = useState(false);
  const [deleteError, setDeleteError] = useState('');
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const accountMenuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handleHashChange = () => {
      setCurrentRoute(getHashRoute());
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

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

  useEffect(() => {
    const handleMouseDown = (event: MouseEvent) => {
      if (!accountMenuRef.current) return;
      if (accountMenuRef.current.contains(event.target as Node)) return;
      setAccountMenuOpen(false);
    };

    window.addEventListener('mousedown', handleMouseDown);
    return () => window.removeEventListener('mousedown', handleMouseDown);
  }, []);

  const accountInitials = useMemo(() => {
    const source = user?.username?.trim() || user?.email?.trim() || 'U';
    return source
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase() ?? '')
      .join('') || 'U';
  }, [user]);

  const handleLogin = (loggedInUser: AuthUser) => {
    setUser(loggedInUser);
    sessionStorage.setItem('ste.currentUser', JSON.stringify(loggedInUser));
    setDeleteOpen(false);
    setAccountMenuOpen(false);
    setDeleteError('');
    setDeletePassword('');
    setDeleteConfirmText('');
    setDeleteEmail(loggedInUser.email);
    window.location.hash = '#dashboard';
  };

  const handleLogout = () => {
    setUser(null);
    sessionStorage.removeItem('ste.currentUser');
    setDeleteOpen(false);
    setAccountMenuOpen(false);
    setDeleteError('');
    setDeletePassword('');
    setDeleteConfirmText('');
    setDeleteEmail('');
    window.location.hash = '#home';
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
    if (currentRoute === 'login') {
      return <LoginPage onLogin={handleLogin} onBackHome={() => { window.location.hash = '#home'; }} />;
    }
    return <HomePage onSignIn={() => { window.location.hash = '#login'; }} />;
  }

  return (
    <main style={{ minHeight: '100vh', background: '#f4f7fb', color: '#17212b', padding: 24, fontFamily: 'Arial, sans-serif' }}>
      <header style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 24 }}>
        <div>
          <h1 style={{ marginBottom: 8 }}>Software Testing Engine</h1>
          <p style={{ margin: 0 }}>Web control plane starter for requirements, generated test cases, and executions.</p>
        </div>
        <div ref={accountMenuRef} style={{ position: 'relative', minWidth: 72, display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
          <button
            type="button"
            onClick={() => setAccountMenuOpen((current) => !current)}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 48,
              height: 48,
              background: '#ffffff',
              border: '3px solid #e2e8f0',
              borderRadius: '50%',
              padding: 0,
              cursor: 'pointer',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)',
            }}
            aria-label="Open account menu"
          >
            <div style={{ width: 38, height: 38, borderRadius: '50%', background: '#5c3ab1', color: '#fff', display: 'grid', placeItems: 'center', fontWeight: 700, flexShrink: 0, fontSize: 16 }}>
              {accountInitials}
            </div>
          </button>

          {accountMenuOpen && (
            <div style={{ position: 'absolute', top: 'calc(100% + 12px)', right: 0, width: 344, background: '#ffffff', border: '1px solid #d7e0ea', borderRadius: 20, boxShadow: '0 18px 40px rgba(16, 24, 40, 0.18)', padding: 16, zIndex: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, paddingBottom: 14, borderBottom: '1px solid #edf2f7' }}>
                <div style={{ width: 52, height: 52, borderRadius: '50%', background: '#5c3ab1', color: '#fff', display: 'grid', placeItems: 'center', fontSize: 20, fontWeight: 700, border: '2px solid #e7e0ff' }}>
                  {accountInitials}
                </div>
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontWeight: 700, fontSize: 16 }}>{user.username}</div>
                  <div style={{ fontSize: 13, color: '#667085', overflow: 'hidden', textOverflow: 'ellipsis' }}>{user.email}</div>
                  <div style={{ marginTop: 4, fontSize: 12, color: '#175cd3', fontWeight: 600 }}>{user.role === 'admin' ? 'Administrator' : 'Standard user'}</div>
                </div>
              </div>

              <div style={{ display: 'grid', gap: 8, marginTop: 14 }}>
                <button type="button" onClick={handleLogout} style={{ width: '100%' }}>
                  Logout
                </button>
                <button
                  type="button"
                  style={{ width: '100%', background: '#b42318', color: '#fff', border: 'none', borderRadius: 8, padding: '8px 10px', cursor: 'pointer', fontWeight: 600 }}
                  onClick={() => {
                    setDeleteOpen((current) => !current);
                    setDeleteError('');
                    setDeletePassword('');
                    setDeleteConfirmText('');
                    setDeleteEmail(user.email);
                  }}
                >
                  {deleteOpen ? 'Hide delete form' : 'Delete my account'}
                </button>
              </div>
            </div>
          )}
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

