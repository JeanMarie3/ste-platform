import { Dashboard } from './pages/Dashboard';

export default function App() {
  return (
    <main style={{ minHeight: '100vh', background: '#f4f7fb', color: '#17212b', padding: 24, fontFamily: 'Arial, sans-serif' }}>
      <header style={{ marginBottom: 24 }}>
        <h1 style={{ marginBottom: 8 }}>Software Testing Engine</h1>
        <p style={{ margin: 0 }}>Web control plane starter for requirements, generated test cases, and executions.</p>
      </header>
      <Dashboard />
    </main>
  );
}
