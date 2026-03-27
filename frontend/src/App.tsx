import { Dashboard } from './pages/Dashboard';
import { useState, useEffect } from 'react';

type AppUser = { username: string; password: string; role: 'admin' | 'standard' };

export default function App() {
  const [user, setUser] = useState<{ username: string; role: 'admin' | 'standard' } | null>(null);

  const [users, setUsers] = useState<AppUser[]>(() => {
    const saved = localStorage.getItem('ste.users');
    if (saved) return JSON.parse(saved);
    return [
      { username: 'admin', password: 'admin', role: 'admin' },
      { username: 'user', password: 'user', role: 'standard' }
    ];
  });

  useEffect(() => {
    localStorage.setItem('ste.users', JSON.stringify(users));
  }, [users]);

  if (!user) {
    return <AuthScreen onLogin={setUser} users={users} setUsers={setUsers} />;
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
          <button style={{ marginTop: 8 }} onClick={() => setUser(null)}>Logout</button>
        </div>
      </header>
      <Dashboard userRole={user.role} />
    </main>
  );
}

function AuthScreen({ onLogin, users, setUsers }: { 
  onLogin: (user: { username: string; role: 'admin' | 'standard' }) => void;
  users: AppUser[];
  setUsers: (users: AppUser[]) => void;
}) {
  const [mode, setMode] = useState<'login' | 'signup' | 'forgot'>('login');
  
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'admin' | 'standard'>('standard');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');
    
    if (!username.trim()) {
      setError('Username is required');
      return;
    }

    if (mode === 'login') {
      const foundUser = users.find(u => u.username === username && u.password === password);
      if (foundUser) {
        onLogin({ username: foundUser.username, role: foundUser.role });
      } else {
        setError('Invalid credentials.');
      }
    } else if (mode === 'signup') {
      if (!password.trim()) {
        setError('Password is required');
        return;
      }
      if (users.some(u => u.username === username)) {
        setError('Username already exists');
        return;
      }
      const newUser: AppUser = { username, password, role };
      setUsers([...users, newUser]);
      setMessage('Account created! You can now log in.');
      setMode('login');
      setPassword('');
    } else if (mode === 'forgot') {
      const foundUser = users.find(u => u.username === username);
      if (!foundUser) {
        setError('Username not found');
        return;
      }
      if (!password.trim()) {
        setError('New password is required');
        return;
      }
      setUsers(users.map(u => u.username === username ? { ...u, password } : u));
      setMessage('Password reset successful! You can now log in.');
      setMode('login');
      setPassword('');
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
        {message && <div style={{ color: 'green', fontSize: 14 }}>{message}</div>}
        
        <input 
          placeholder="Username" 
          value={username} 
          onChange={e => setUsername(e.target.value)} 
          style={{ padding: 8, border: '1px solid #ccc', borderRadius: 4 }}
        />
        
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
          placeholder={mode === 'forgot' ? "New Password" : "Password"}
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
            <span style={{ color: '#0066cc', cursor: 'pointer' }} onClick={() => { setMode('login'); setError(''); setMessage(''); setPassword(''); }}>Back to Login</span>
          ) : (
            <>
              <span style={{ color: '#0066cc', cursor: 'pointer' }} onClick={() => { setMode('signup'); setError(''); setMessage(''); setPassword(''); }}>Create Account</span>
              <span style={{ color: '#0066cc', cursor: 'pointer' }} onClick={() => { setMode('forgot'); setError(''); setMessage(''); setPassword(''); }}>Forgot Password?</span>
            </>
          )}
        </div>
      </form>
    </div>
  );
}
