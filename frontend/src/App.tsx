import { Dashboard } from './pages/Dashboard';
import { useState } from 'react';

export default function App() {
  const [user, setUser] = useState<{ username: string; role: 'admin' | 'standard' } | null>(null);

  if (!user) {
    return <Login onLogin={setUser} />;
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

function Login({ onLogin }: { onLogin: (user: { username: string; role: 'admin' | 'standard' }) => void }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (username === 'admin' && password === 'admin') {
      onLogin({ username, role: 'admin' });
    } else if (username === 'user' && password === 'user') {
      onLogin({ username, role: 'standard' });
    } else {
      setError('Invalid credentials. Use admin/admin or user/user.');
    }
  };

  return (
    <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f4f7fb', fontFamily: 'Arial, sans-serif' }}>
      <form onSubmit={handleLogin} style={{ background: 'white', padding: 32, borderRadius: 8, boxShadow: '0 4px 12px rgba(0,0,0,0.1)', display: 'grid', gap: 16, width: 300 }}>
        <h2 style={{ margin: 0, textAlign: 'center' }}>Login</h2>
        {error && <div style={{ color: 'red', fontSize: 14 }}>{error}</div>}
        <input 
          placeholder="Username" 
          value={username} 
          onChange={e => setUsername(e.target.value)} 
          style={{ padding: 8, border: '1px solid #ccc', borderRadius: 4 }}
        />
        <input 
          type="password" 
          placeholder="Password" 
          value={password} 
          onChange={e => setPassword(e.target.value)} 
          style={{ padding: 8, border: '1px solid #ccc', borderRadius: 4 }}
        />
        <button type="submit" style={{ padding: 10, background: '#0066cc', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer' }}>
          Login
        </button>
      </form>
    </div>
  );
}
