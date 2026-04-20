import React, { useEffect, useState } from 'react';
import { apiDelete, apiGet, apiPost } from '../api/client';
import { AuthUser } from '../types';

export function UserManagement() {
  const [users, setUsers] = useState<AuthUser[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    role: 'standard',
  });

  const loadUsers = async () => {
    setBusy(true);
    setError('');
    try {
      const data = await apiGet<AuthUser[]>('/auth/users');
      setUsers(data);
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError('');
    setSuccess('');
    // Mock the email for now if we're mimicking the screenshot which only has username/password
    const emailToUse = form.email || `${form.username}@example.com`;
    try {
      await apiPost<AuthUser>('/auth/users', { ...form, email: emailToUse });
      setSuccess('User created successfully');
      setForm({ username: '', email: '', password: '', role: 'standard' });
      await loadUsers();
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy(false);
    }
  };

  const handleDeleteUser = async (userId: string, username: string) => {
    if (!window.confirm(`Are you sure you want to delete user "${username}"?`)) return;

    setBusy(true);
    setError('');
    setSuccess('');
    try {
      await apiDelete(`/auth/users/${userId}`);
      setSuccess('User deleted successfully');
      await loadUsers();
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', background: '#fff', borderRadius: 8, padding: 32, boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
      <h2 style={{ textAlign: 'center', fontSize: 32, marginBottom: 32, fontWeight: 'normal' }}>Manage Users</h2>

      {error && <div style={{ color: '#b42318', background: '#fef3f2', padding: 12, borderRadius: 6, marginBottom: 24 }}>{error}</div>}
      {success && <div style={{ color: '#027a48', background: '#ecfdf3', padding: 12, borderRadius: 6, marginBottom: 24 }}>{success}</div>}

      <form onSubmit={handleCreateUser} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 16, marginBottom: 48, alignItems: 'center' }}>
        <input
          required
          value={form.username}
          onChange={e => setForm({ ...form, username: e.target.value })}
          style={{ padding: 12, border: '1px solid #d0d5dd', borderRadius: 4, width: '100%', fontSize: 16 }}
          placeholder="New Username"
        />
        <input
          required
          type="text"
          value={form.password}
          onChange={e => setForm({ ...form, password: e.target.value })}
          style={{ padding: 12, border: '1px solid #d0d5dd', borderRadius: 4, width: '100%', fontSize: 16 }}
          placeholder="New Password"
          minLength={4}
        />
        <button
          type="submit"
          disabled={busy}
          style={{
            background: '#527bbd',
            color: '#fff',
            border: 'none',
            padding: '12px 24px',
            borderRadius: 4,
            cursor: busy ? 'not-allowed' : 'pointer',
            fontSize: 16,
            minWidth: 120
          }}
        >
          {busy ? 'Creating...' : 'Create'}
        </button>
      </form>

      <h3 style={{ fontSize: 20, marginBottom: 16, fontWeight: 'normal' }}>Existing Users</h3>
      <div style={{ border: '1px solid #e2e8f0', borderRadius: 8 }}>
        {users.map((u, i) => (
          <div
            key={u.id}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: 16,
              borderBottom: i < users.length - 1 ? '1px solid #e2e8f0' : 'none'
            }}
          >
            <span style={{ fontWeight: 'bold' }}>{u.username}</span>
            <button
              onClick={() => handleDeleteUser(u.id, u.username)}
              disabled={busy}
              style={{
                background: '#ca5c54',
                color: '#fff',
                border: 'none',
                padding: '8px 16px',
                borderRadius: 4,
                cursor: busy ? 'not-allowed' : 'pointer',
                fontSize: 14,
              }}
            >
              Delete
            </button>
          </div>
        ))}
        {users.length === 0 && (
          <div style={{ padding: 24, textAlign: 'center', color: '#667085' }}>No users found</div>
        )}
      </div>
    </div>
  );
}


