import { FormEvent, useEffect, useMemo, useState } from 'react';

import { apiGet, apiPost } from '../api/client';
import { Panel } from '../components/Panel';
import type { AISuggestion, Platform, Requirement, TestCase, TestRun } from '../types';

const priorities = ['low', 'medium', 'high'];
const risks = ['low', 'medium', 'high'];
const reviewStatuses = ['under_review', 'approved', 'rejected', 'needs_update'];

export function Dashboard() {
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [testCases, setTestCases] = useState<TestCase[]>([]);
  const [runs, setRuns] = useState<TestRun[]>([]);
  const [busy, setBusy] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [aiText, setAiText] = useState<string>('');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiNote, setAiNote] = useState<string>('');
  const [form, setForm] = useState({
    title: 'Login requirement',
    description: 'User can log in successfully and reach the dashboard with the expected feature area visible.',
    priority: 'high',
    risk: 'high',
    business_rules: 'Lock account after five failed attempts',
  });

  const selectedPlatforms = useMemo(() => ['web', 'api'] as Platform[], []);

  // Lookup maps for relationship labels
  const requirementById = useMemo(() => {
    const m: Record<string, Requirement> = {};
    for (const r of requirements) m[r.id] = r;
    return m;
  }, [requirements]);

  const testCaseById = useMemo(() => {
    const m: Record<string, TestCase> = {};
    for (const tc of testCases) m[tc.id] = tc;
    return m;
  }, [testCases]);

  const runsByTestCase = useMemo(() => {
    const grouped: Array<{ testCaseId: string; runs: TestRun[] }> = [];
    const indexByTestCaseId: Record<string, number> = {};

    for (const run of runs) {
      const existingIndex = indexByTestCaseId[run.test_case_id];
      if (existingIndex === undefined) {
        indexByTestCaseId[run.test_case_id] = grouped.length;
        grouped.push({ testCaseId: run.test_case_id, runs: [run] });
      } else {
        grouped[existingIndex].runs.push(run);
      }
    }

    return grouped;
  }, [runs]);

  const testCasesByRequirement = useMemo(() => {
    const grouped: Array<{ requirementId: string; cases: TestCase[] }> = [];
    const indexByRequirementId: Record<string, number> = {};

    for (const tc of testCases) {
      const existingIndex = indexByRequirementId[tc.requirement_id];
      if (existingIndex === undefined) {
        indexByRequirementId[tc.requirement_id] = grouped.length;
        grouped.push({ requirementId: tc.requirement_id, cases: [tc] });
      } else {
        grouped[existingIndex].cases.push(tc);
      }
    }

    return grouped;
  }, [testCases]);

  const requirementNumberById = useMemo(() => {
    const labels: Record<string, string> = {};
    const requirementIds = Array.from(new Set(testCases.map((tc) => tc.requirement_id))).sort();
    requirementIds.forEach((requirementId, index) => {
      labels[requirementId] = String(index + 1).padStart(4, '0');
    });
    return labels;
  }, [testCases]);

  const testCaseVersionById = useMemo(() => {
    const labels: Record<string, string> = {};
    testCasesByRequirement.forEach((group) => {
      const tcNumber = requirementNumberById[group.requirementId] ?? '0000';
      group.cases.forEach((testCase, caseIndex) => {
        labels[testCase.id] = `TC-${tcNumber}-v${caseIndex + 1}`;
      });
    });
    return labels;
  }, [testCasesByRequirement, requirementNumberById]);

  const getExecutionLabel = (index: number): string => `execution-${String(index + 1).padStart(2, '0')}`;

  const refresh = async () => {
    const [requirementsData, testCasesData, runsData] = await Promise.all([
      apiGet<Requirement[]>('/requirements'),
      apiGet<TestCase[]>('/testcases'),
      apiGet<TestRun[]>('/executions'),
    ]);
    setRequirements(requirementsData);
    setTestCases(testCasesData);
    setRuns(runsData);
  };

  useEffect(() => {
    refresh().catch((err) => setError(String(err)));
  }, []);

  const handleAiSuggest = async () => {
    if (!aiText.trim()) return;
    setAiLoading(true);
    setAiNote('');
    try {
      const suggestion = await apiPost<AISuggestion>('/ai/suggest-requirement', { description: aiText });
      if (!suggestion.ai_available) {
        setAiNote('OpenAI key not configured — add OPENAI_API_KEY to your .env file.');
        return;
      }
      setForm({
        title: suggestion.title,
        description: suggestion.description,
        priority: suggestion.priority,
        risk: suggestion.risk,
        business_rules: suggestion.business_rules.join('\n'),
      });
      setAiNote('✓ Form pre-filled by AI — review and submit.');
      setAiText('');
    } catch (err) {
      setAiNote(`AI error: ${String(err)}`);
    } finally {
      setAiLoading(false);
    }
  };

  const handleCreateRequirement = async (event: FormEvent) => {
    event.preventDefault();
    setBusy('requirement');
    setError('');
    try {
      await apiPost<Requirement>('/requirements', {
        ...form,
        platforms: selectedPlatforms,
        business_rules: form.business_rules.split('\n').map((item) => item.trim()).filter(Boolean),
      });
      await refresh();
      setForm({ ...form, title: '', description: '', business_rules: '' });
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy('');
    }
  };

  const generateTestCases = async (requirementId: string) => {
    setBusy(requirementId);
    setError('');
    try {
      await apiPost<TestCase[]>(`/requirements/${requirementId}/generate-testcases`);
      await refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy('');
    }
  };

  const reviewTestCase = async (testCaseId: string, review_status: string) => {
    setBusy(testCaseId);
    setError('');
    try {
      await apiPost<TestCase>(`/testcases/${testCaseId}/review`, {
        review_status,
        comment: `Updated to ${review_status} in dashboard`,
      });
      await refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy('');
    }
  };

  const startExecution = async (testCase: TestCase) => {
    setBusy(`run-${testCase.id}`);
    setError('');
    try {
      await apiPost<TestRun>('/executions/start', {
        test_case_id: testCase.id,
        agent_type: testCase.platform,
        environment: 'local',
      });
      await refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy('');
    }
  };

  const runsByTC = useMemo(() => {
    const tcGroupMap: Record<string, Array<{ tcVersion: string; runs: TestRun[] }>> = {};
    
    for (const group of runsByTestCase) {
      const tcVersion = testCaseVersionById[group.testCaseId] ?? group.testCaseId;
      // Extract base TC number (e.g., "TC-0001" from "TC-0001-v2")
      const tcBaseMatch = tcVersion.match(/^(TC-\d+)/);
      const tcBase = tcBaseMatch ? tcBaseMatch[1] : 'TC-0000';
      
      if (!tcGroupMap[tcBase]) {
        tcGroupMap[tcBase] = [];
      }
      tcGroupMap[tcBase].push({ tcVersion, runs: group.runs });
    }

    // Sort each TC's versions by version number descending (latest first)
    const sorted: Array<{ tcBase: string; versions: Array<{ tcVersion: string; runs: TestRun[] }> }> = [];
    Object.keys(tcGroupMap)
      .sort()
      .forEach((tcBase) => {
        sorted.push({
          tcBase,
          versions: tcGroupMap[tcBase].sort((a, b) => {
            const aVer = parseInt(a.tcVersion.split('-v')[1] || '0', 10);
            const bVer = parseInt(b.tcVersion.split('-v')[1] || '0', 10);
            return bVer - aVer; // Descending
          }),
        });
      });

    return sorted;
  }, [runsByTestCase, testCaseVersionById]);

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      {error ? <div style={{ padding: 12, background: '#fdecec', border: '1px solid #f4b1b1', borderRadius: 8 }}>{error}</div> : null}

      <Panel title="✦ AI Assist — Describe your requirement">
        <div style={{ display: 'grid', gap: 10 }}>
          <textarea
            value={aiText}
            placeholder="Describe what needs to be tested in plain English, e.g. 'Users should be able to reset their password via email link within 10 minutes, with rate limiting to 3 attempts per hour.'"
            rows={3}
            onChange={(e) => setAiText(e.target.value)}
          />
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button onClick={handleAiSuggest} disabled={aiLoading || !aiText.trim()}>
              {aiLoading ? 'Thinking...' : 'Suggest with AI ✦'}
            </button>
            {aiNote ? (
              <span style={{ fontSize: 13, color: aiNote.startsWith('✓') ? '#2d7a3a' : '#b05c00' }}>{aiNote}</span>
            ) : null}
          </div>
        </div>
      </Panel>

      <Panel title="Create Requirement">
        <form onSubmit={handleCreateRequirement} style={{ display: 'grid', gap: 12 }}>
          <input value={form.title} placeholder="Requirement title" onChange={(e) => setForm({ ...form, title: e.target.value })} />
          <textarea value={form.description} placeholder="Requirement description" rows={4} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <div style={{ display: 'flex', gap: 12 }}>
            <select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}>
              {priorities.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
            <select value={form.risk} onChange={(e) => setForm({ ...form, risk: e.target.value })}>
              {risks.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </div>
          <div>Platforms: {selectedPlatforms.join(', ')}</div>
          <textarea value={form.business_rules} placeholder="Business rules, one per line" rows={3} onChange={(e) => setForm({ ...form, business_rules: e.target.value })} />
          <button type="submit" disabled={busy === 'requirement'}>{busy === 'requirement' ? 'Creating...' : 'Create requirement'}</button>
        </form>
      </Panel>

      <div style={{ display: 'grid', gap: 16, gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))' }}>

        {/* ── Requirements ────────────────────────────────── */}
        <Panel title="Requirements">
          {requirements.length === 0 ? <p>No requirements yet.</p> : requirements.map((item) => (
            <div key={item.id} style={{ marginBottom: 16, paddingBottom: 16, borderBottom: '1px solid #e3e8ef' }}>
              <strong>{item.title}</strong>
              <div style={{ fontSize: 11, color: '#8a96a3', marginBottom: 4 }}>{item.id}</div>
              <div style={{ margin: '4px 0' }}>{item.description}</div>
              <div>{item.platforms.join(', ')} | {item.priority} / {item.risk}</div>
              <button onClick={() => generateTestCases(item.id)} disabled={busy === item.id} style={{ marginTop: 8 }}>
                {busy === item.id ? 'Generating...' : 'Generate test cases'}
              </button>
            </div>
          ))}
        </Panel>

        {/* ── Test Cases — grouped by Requirement ── */}
        <Panel title="Test Cases">
          {testCases.length === 0 ? <p>No test cases yet.</p> : testCasesByRequirement.map((group) => {
            const parentReq = requirementById[group.requirementId];

            return (
              <details key={group.requirementId} style={{ marginBottom: 20, paddingBottom: 12, paddingLeft: 0, borderBottom: '1px solid #d9e1ec' }}>
                <summary style={{ cursor: 'pointer', listStylePosition: 'inside' }}>
                  <span style={{ fontSize: 12, fontWeight: 600 }}>
                    Requirement: {parentReq ? parentReq.title : `Missing requirement (${group.requirementId})`} ({group.cases.length} test case{group.cases.length > 1 ? 's' : ''})
                  </span>
                </summary>

                <div style={{ marginLeft: 40 }}>
                  <div style={{ fontSize: 11, margin: '8px 0' }}>
                    {parentReq ? (
                      <span style={{ background: '#e8f4fd', color: '#1565c0', borderRadius: 4, padding: '1px 6px' }}>
                        {group.requirementId}
                      </span>
                    ) : (
                      <span style={{ background: '#fff3cd', color: '#8a6d3b', borderRadius: 4, padding: '1px 6px' }}>
                        Requirement not found
                      </span>
                    )}
                  </div>

                  {[...group.cases].reverse().map((item) => (
                    <div key={item.id} style={{ marginBottom: 16, paddingBottom: 16, borderBottom: '1px solid #e3e8ef' }}>
                      <div><strong>{testCaseVersionById[item.id] ?? 'TC-0000-v1'}</strong></div>
                      <div style={{ fontSize: 12, color: '#6f7c8a', marginBottom: 2 }}>{item.title}</div>
                      <div style={{ display: 'flex', gap: 6, alignItems: 'center', margin: '4px 0' }}>
                        <span>{item.platform} | {item.review_status}</span>
                        {item.metadata?.ai_generated ? <span style={{ fontSize: 11, background: '#e8f4fd', color: '#1565c0', padding: '1px 6px', borderRadius: 10 }}>AI</span> : null}
                      </div>
                      <div style={{ margin: '4px 0' }}>{item.objective}</div>
                      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 6 }}>
                        {reviewStatuses.map((status) => (
                          <button key={status} onClick={() => reviewTestCase(item.id, status)} disabled={busy === item.id || item.review_status === status}>
                            {status}
                          </button>
                        ))}
                        <button onClick={() => startExecution(item)} disabled={busy === `run-${item.id}` || item.review_status !== 'approved'}>
                          {busy === `run-${item.id}` ? 'Running...' : 'Start execution'}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </details>
            );
          })}
        </Panel>

        {/* ── Executions — grouped by test case ── */}
        <Panel title="Executions">
          {runs.length === 0 ? <p>No test runs yet.</p> : runsByTC.map((tcGroup) => {
            return (
              <details key={tcGroup.tcBase} style={{ marginBottom: 20, paddingBottom: 12, paddingLeft: 0, borderBottom: '1px solid #d9e1ec' }}>
                <summary style={{ cursor: 'pointer', listStylePosition: 'inside' }}>
                  <span style={{ fontSize: 12, fontWeight: 600 }}>{tcGroup.tcBase} ({tcGroup.versions.length} version{tcGroup.versions.length > 1 ? 's' : ''})</span>
                </summary>

                <div style={{ marginLeft: 40 }}>
                  {tcGroup.versions.map((versionGroup) => {
                    const parentTC = testCaseById[Object.entries(testCaseVersionById).find(([, label]) => label === versionGroup.tcVersion)?.[0] || ''];
                    const parentReq = parentTC ? requirementById[parentTC.requirement_id] : undefined;

                    return (
                      <details key={versionGroup.tcVersion} style={{ marginBottom: 16, paddingBottom: 12, paddingLeft: 0, borderBottom: '1px solid #e3e8ef' }}>
                        <summary style={{ cursor: 'pointer', listStylePosition: 'inside', fontSize: 11 }}>
                          <span style={{ fontWeight: 500 }}>
                            {versionGroup.tcVersion} ({versionGroup.runs.length} run{versionGroup.runs.length > 1 ? 's' : ''})
                          </span>
                        </summary>

                        <div style={{ marginLeft: 20 }}>
                          {/* test case group breadcrumb */}
                          {(parentReq || parentTC) && (
                            <div style={{ fontSize: 11, margin: '8px 0' }}>
                              {parentReq && (
                                <span style={{ background: '#e8f4fd', color: '#1565c0', borderRadius: 4, padding: '1px 6px', marginRight: 4 }}>
                                  {parentReq.title}
                                </span>
                              )}
                              {parentTC && (
                                <span style={{ background: '#edf7ed', color: '#2d7a3a', borderRadius: 4, padding: '1px 6px' }}>
                                  ↳ {versionGroup.tcVersion}
                                </span>
                              )}
                            </div>
                          )}

                          {[...versionGroup.runs].reverse().map((item, runIndex) => (
                            <div key={item.id} style={{ marginBottom: 14, paddingBottom: 14, borderBottom: '1px solid #e3e8ef' }}>
                              <div><strong>{getExecutionLabel(versionGroup.runs.length - runIndex - 1)}</strong></div>
                              <div>{item.status} | Confidence: {item.confidence_score.toFixed(2)}</div>
                              <div style={{ margin: '4px 0', fontSize: 13 }}>{item.summary_reason}</div>
                              <details>
                                <summary style={{ cursor: 'pointer', fontSize: 13 }}>Step details</summary>
                                <ul>
                                  {item.steps.map((step) => (
                                    <li key={`${item.id}-${step.step_number}`}>
                                      {step.action} {'→'} {step.verdict.status} ({step.verdict.reason})
                                    </li>
                                  ))}
                                </ul>
                              </details>
                            </div>
                          ))}
                        </div>
                      </details>
                    );
                  })}
                </div>
              </details>
            );
          })}
        </Panel>

      </div>
    </div>
  );
}
