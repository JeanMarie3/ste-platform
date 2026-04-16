import { PropsWithChildren } from 'react';

interface PanelProps extends PropsWithChildren {
  title: string;
}

export function Panel({ title, children }: PanelProps) {
  return (
    <section style={{ background: '#fff', borderRadius: 12, padding: 16, boxShadow: '0 2px 8px rgba(0,0,0,0.08)', display: 'flex', flexDirection: 'column', height: '100%' }}>
      <h2 style={{ marginTop: 0 }}>{title}</h2>
      <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
        {children}
      </div>
    </section>
  );
}
