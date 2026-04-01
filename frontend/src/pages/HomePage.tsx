import type { CSSProperties } from 'react';

interface HomePageProps {
  onSignIn: () => void;
}

export function HomePage({ onSignIn }: HomePageProps) {
  const menuLinkStyle: CSSProperties = {
    color: '#2b3f55',
    textDecoration: 'none',
    fontWeight: 600,
    fontSize: 14,
  };

  return (
    <main style={{ minHeight: '100vh', background: '#f4f7fb', color: '#17212b', fontFamily: 'Arial, sans-serif' }}>
      <header style={{ position: 'sticky', top: 0, zIndex: 10, background: '#ffffff', borderBottom: '1px solid #e4e8ef' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto', padding: '14px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ fontSize: 20, fontWeight: 700 }}>Software Testing Engine</div>
          <nav style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
            <a href="#home" style={menuLinkStyle}>Home</a>
            <a href="#features" style={menuLinkStyle}>Features</a>
            <a href="#workflow" style={menuLinkStyle}>Workflow</a>
            <a href="#security" style={menuLinkStyle}>Security</a>
            <a href="#contact" style={menuLinkStyle}>Contact</a>
            <button onClick={onSignIn} style={{ background: '#175cd3', color: '#fff', border: 'none', borderRadius: 6, padding: '8px 14px', cursor: 'pointer', fontWeight: 600 }}>
              Sign In
            </button>
          </nav>
        </div>
      </header>

      <section style={{ maxWidth: 1100, margin: '0 auto', padding: '64px 20px 42px' }}>
        <div style={{ maxWidth: 720 }}>
          <h1 style={{ margin: 0, fontSize: 44, lineHeight: 1.15 }}>Deliver higher-quality releases with AI-assisted test operations.</h1>
          <p style={{ marginTop: 18, fontSize: 18, color: '#4a6178', lineHeight: 1.6 }}>
            STE centralizes requirements, auto-generates test cases, and executes runs in one secure control plane so teams can ship with confidence.
          </p>
          <div style={{ marginTop: 26, display: 'flex', gap: 12 }}>
            <button onClick={onSignIn} style={{ background: '#175cd3', color: '#fff', border: 'none', borderRadius: 6, padding: '11px 18px', cursor: 'pointer', fontWeight: 600 }}>
              Get Started
            </button>
            <a href="#features" style={{ display: 'inline-block', border: '1px solid #cfd7e3', borderRadius: 6, padding: '10px 18px', textDecoration: 'none', color: '#203449', fontWeight: 600 }}>
              View Features
            </a>
          </div>
        </div>
      </section>

      <section id="features" style={{ maxWidth: 1100, margin: '0 auto', padding: '8px 20px 36px' }}>
        <h2 style={{ fontSize: 30, marginBottom: 14 }}>Why teams choose STE</h2>
        <div style={{ display: 'grid', gap: 14, gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))' }}>
          <FeatureCard title="Requirement Intelligence" text="Capture, structure, and prioritize requirements with AI-assisted drafting and consistency checks." />
          <FeatureCard title="Automated Test Design" text="Generate comprehensive, reviewable test cases from each approved requirement." />
          <FeatureCard title="Execution Visibility" text="Track verdicts, confidence scores, and step-level evidence across all executions." />
          <FeatureCard title="Role-Aware Controls" text="Support secure collaboration with admin-managed actions and controlled user lifecycle." />
        </div>
      </section>

      <section id="workflow" style={{ maxWidth: 1100, margin: '0 auto', padding: '8px 20px 36px' }}>
        <h2 style={{ fontSize: 30, marginBottom: 14 }}>Simple end-to-end workflow</h2>
        <div style={{ display: 'grid', gap: 10 }}>
          <WorkflowItem step="1" title="Define requirements" text="Document testable business outcomes with platform, priority, and risk context." />
          <WorkflowItem step="2" title="Generate and review test cases" text="Use AI support to accelerate coverage and review status decisions." />
          <WorkflowItem step="3" title="Run executions and decide" text="Start runs, monitor confidence, and act on clear verdict explanations." />
        </div>
      </section>

      <section id="security" style={{ maxWidth: 1100, margin: '0 auto', padding: '8px 20px 52px' }}>
        <h2 style={{ fontSize: 30, marginBottom: 14 }}>Security and governance</h2>
        <p style={{ maxWidth: 760, color: '#4a6178', lineHeight: 1.7 }}>
          STE stores users in backend SQLite with credential verification, supports protected account deletion with confirmation, and keeps admin creation under backend control.
        </p>
      </section>

      <footer id="contact" style={{ borderTop: '1px solid #e4e8ef', background: '#ffffff' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto', padding: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <div style={{ color: '#5a7088' }}>Software Testing Engine</div>
          <div style={{ color: '#5a7088' }}>Need a walkthrough? Contact your platform administrator.</div>
        </div>
      </footer>
    </main>
  );
}

function FeatureCard({ title, text }: { title: string; text: string }) {
  return (
    <article style={{ background: '#ffffff', border: '1px solid #dbe3ef', borderRadius: 10, padding: 16 }}>
      <h3 style={{ margin: 0, marginBottom: 8, fontSize: 18 }}>{title}</h3>
      <p style={{ margin: 0, color: '#4a6178', lineHeight: 1.6 }}>{text}</p>
    </article>
  );
}

function WorkflowItem({ step, title, text }: { step: string; title: string; text: string }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '40px 1fr', gap: 12, alignItems: 'start', background: '#ffffff', border: '1px solid #dbe3ef', borderRadius: 10, padding: 14 }}>
      <div style={{ width: 32, height: 32, borderRadius: 999, background: '#175cd3', color: '#fff', display: 'grid', placeItems: 'center', fontWeight: 700 }}>
        {step}
      </div>
      <div>
        <h3 style={{ margin: 0, marginBottom: 6, fontSize: 18 }}>{title}</h3>
        <p style={{ margin: 0, color: '#4a6178', lineHeight: 1.6 }}>{text}</p>
      </div>
    </div>
  );
}
