import { CSSProperties, FormEvent, useEffect, useMemo, useRef, useState } from 'react';

import { apiDelete, apiGet, apiPost } from '../api/client';
import { Panel } from '../components/Panel';
import { formatDateTime } from '../utils/formatters';
import type { AISuggestion, Platform, Requirement, StartExecutionRequest, TestCase, TestRun } from '../types';

const priorities = ['low', 'medium', 'high'];
const risks = ['low', 'medium', 'high'];
const reviewStatuses = ['under_review', 'approved', 'rejected', 'needs_update'];
const platformOptions: Platform[] = ['web', 'api', 'database', 'mobile', 'desktop'];
const initialSelectedPlatforms: Platform[] = [];

const isValidHttpUrl = (value: string): boolean => {
  try {
    const parsed = new URL(value);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:';
  } catch {
    return false;
  }
};

const initialRequirementForm = {
  project_code: '',
  title: '',
  description: '',
  target_url: '',
  priority: 'high',
  risk: 'high',
  business_rules: '',
};

export interface DashboardProps {
  userRole?: 'admin' | 'standard';
}

export function Dashboard({ userRole }: DashboardProps) {
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [testCases, setTestCases] = useState<TestCase[]>([]);
  const [runs, setRuns] = useState<TestRun[]>([]);
  const [busy, setBusy] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [aiText, setAiText] = useState<string>('');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiNote, setAiNote] = useState<string>('');
  const [aiApiKey, setAiApiKey] = useState<string>(() => localStorage.getItem('ste.openaiApiKey') ?? '');
  const [executionHeadless, setExecutionHeadless] = useState<boolean>(true);
  const [form, setForm] = useState(initialRequirementForm);
  const [highlightedRunId, setHighlightedRunId] = useState<string | null>(null);
  const highlightTimerRef = useRef<number | null>(null);

  const [selectedPlatforms, setSelectedPlatforms] = useState<Platform[]>(initialSelectedPlatforms);

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

  const requirementsByProject = useMemo(() => {
    const grouped: Array<{ projectCode: string; items: Requirement[] }> = [];
    const indexByProjectCode: Record<string, number> = {};

    for (const requirement of requirements) {
      const projectCode = requirement.project_code?.trim() || 'UNSPECIFIED';
      const existingIndex = indexByProjectCode[projectCode];
      if (existingIndex === undefined) {
        indexByProjectCode[projectCode] = grouped.length;
        grouped.push({ projectCode, items: [requirement] });
      } else {
        grouped[existingIndex].items.push(requirement);
      }
    }

    return grouped.sort((a, b) => a.projectCode.localeCompare(b.projectCode));
  }, [requirements]);

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

  const testCasesByProject = useMemo(() => {
    const grouped: Array<{ projectCode: string; totalCases: number; tcGroups: Array<{ tcBase: string; versions: TestCase[] }> }> = [];
    const projectIndexByCode: Record<string, number> = {};
    const tcIndexByProject: Record<string, Record<string, number>> = {};

    for (const item of testCases) {
      const parentRequirement = requirementById[item.requirement_id];
      const projectCode = parentRequirement?.project_code?.trim() || 'UNSPECIFIED';
      const tcVersion = testCaseVersionById[item.id] ?? item.id;
      const tcBaseMatch = tcVersion.match(/^(TC-\d+)/);
      const tcBase = tcBaseMatch ? tcBaseMatch[1] : 'TC-0000';

      let projectIdx = projectIndexByCode[projectCode];
      if (projectIdx === undefined) {
        projectIdx = grouped.length;
        projectIndexByCode[projectCode] = projectIdx;
        grouped.push({ projectCode, totalCases: 0, tcGroups: [] });
        tcIndexByProject[projectCode] = {};
      }

      grouped[projectIdx].totalCases += 1;

      const tcGroupIndex = tcIndexByProject[projectCode][tcBase];
      if (tcGroupIndex === undefined) {
        tcIndexByProject[projectCode][tcBase] = grouped[projectIdx].tcGroups.length;
        grouped[projectIdx].tcGroups.push({ tcBase, versions: [item] });
      } else {
        grouped[projectIdx].tcGroups[tcGroupIndex].versions.push(item);
      }
    }

    return grouped
      .map((projectGroup) => ({
        ...projectGroup,
        tcGroups: projectGroup.tcGroups
          .map((tcGroup) => ({
            ...tcGroup,
            versions: [...tcGroup.versions].sort((a, b) => {
              const aVer = parseInt((testCaseVersionById[a.id] ?? '').split('-v')[1] || '0', 10);
              const bVer = parseInt((testCaseVersionById[b.id] ?? '').split('-v')[1] || '0', 10);
              return bVer - aVer;
            }),
          }))
          .sort((a, b) => a.tcBase.localeCompare(b.tcBase)),
      }))
      .sort((a, b) => a.projectCode.localeCompare(b.projectCode));
  }, [testCases, requirementById, testCaseVersionById]);

  const getExecutionLabel = (runOrder: number): string => `execution-${String(Math.max(runOrder, 1)).padStart(2, '0')}`;

  const latestRunByTestCaseId = useMemo(() => {
    const latest: Record<string, TestRun> = {};
    for (const run of runs) {
      const current = latest[run.test_case_id];
      if (!current) {
        latest[run.test_case_id] = run;
        continue;
      }
      if (new Date(run.started_at).getTime() > new Date(current.started_at).getTime()) {
        latest[run.test_case_id] = run;
      }
    }
    return latest;
  }, [runs]);

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

  useEffect(() => {
    if (aiApiKey.trim()) {
      localStorage.setItem('ste.openaiApiKey', aiApiKey.trim());
    } else {
      localStorage.removeItem('ste.openaiApiKey');
    }
  }, [aiApiKey]);

  useEffect(() => {
    return () => {
      if (highlightTimerRef.current !== null) {
        window.clearTimeout(highlightTimerRef.current);
      }
    };
  }, []);

  const aiHeaders = aiApiKey.trim() ? { 'X-OpenAI-Api-Key': aiApiKey.trim() } : undefined;

  const handleAiSuggest = async () => {
    if (!aiText.trim()) return;
    setAiLoading(true);
    setAiNote('');
    try {
      const suggestion = await apiPost<AISuggestion>(
        '/ai/suggest-requirement',
        { description: aiText },
        { headers: aiHeaders },
      );
      if (!suggestion.ai_available) {
        setAiNote('No AI key available. Add your own key above or configure OPENAI_API_KEY on the server.');
        return;
      }
      setForm({
        project_code: form.project_code,
        title: suggestion.title,
        description: suggestion.description,
        target_url: form.target_url,
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
    if (selectedPlatforms.length === 0) {
      setError('Select at least one platform.');
      return;
    }
    const normalizedTargetUrl = form.target_url.trim();
    if (selectedPlatforms.includes('web') && !normalizedTargetUrl) {
      setError('Target web application URL is required when web platform is selected.');
      return;
    }
    if (normalizedTargetUrl && !isValidHttpUrl(normalizedTargetUrl)) {
      setError('Target URL must be a valid http/https URL.');
      return;
    }
    setBusy('requirement');
    setError('');
    try {
      await apiPost<Requirement>('/requirements', {
        ...form,
        target_url: normalizedTargetUrl || null,
        platforms: selectedPlatforms,
        business_rules: form.business_rules.split('\n').map((item) => item.trim()).filter(Boolean),
      });
      await refresh();
      setForm(initialRequirementForm);
      setSelectedPlatforms(initialSelectedPlatforms);
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
      await apiPost<TestCase[]>(`/requirements/${requirementId}/generate-testcases`, undefined, { headers: aiHeaders });
      await refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy('');
    }
  };

  const deleteRequirement = async (requirementId: string) => {
    const confirmed = window.confirm(`Delete requirement ${requirementId}? This will also delete all test cases and executions under it.`);
    if (!confirmed) return;

    setBusy(`delete-req-${requirementId}`);
    setError('');
    try {
      await apiDelete(`/requirements/${requirementId}`);
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
      const payload: StartExecutionRequest = {
        test_case_id: testCase.id,
        agent_type: testCase.platform,
        environment: 'local',
        headless: testCase.platform === 'web' ? executionHeadless : true,
      };
      await apiPost<TestRun>('/executions/start', payload);
      await refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy('');
    }
  };

  const deleteTestCase = async (testCase: TestCase) => {
    const tcLabel = testCaseVersionById[testCase.id] ?? testCase.id;
    const confirmed = window.confirm(`Delete ${tcLabel}? This will also delete all executions under it.`);
    if (!confirmed) return;

    setBusy(`delete-${testCase.id}`);
    setError('');
    try {
      await apiDelete(`/testcases/${testCase.id}`);
      await refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy('');
    }
  };

  const deleteExecution = async (run: TestRun) => {
    const confirmed = window.confirm(`Delete execution ${run.id}? This action cannot be undone.`);
    if (!confirmed) return;

    setBusy(`delete-run-${run.id}`);
    setError('');
    try {
      await apiDelete(`/executions/${run.id}`);
      await refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy('');
    }
  };

  const togglePlatform = (platform: Platform) => {
    setSelectedPlatforms((current) => (
      current.includes(platform)
        ? current.filter((item) => item !== platform)
        : [...current, platform]
    ));
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

  const getTestCaseResultBadge = (testCaseId: string): { label: string; style: CSSProperties } => {
    const latestRun = latestRunByTestCaseId[testCaseId];
    if (!latestRun) {
      return {
        label: 'Not run',
        style: { background: '#f2f4f7', color: '#475467' },
      };
    }

    if (latestRun.status === 'passed') {
      return {
        label: 'Passed',
        style: { background: '#e8f5e9', color: '#1b5e20' },
      };
    }

    if (latestRun.status === 'failed') {
      return {
        label: 'Failed',
        style: { background: '#ffebee', color: '#b71c1c' },
      };
    }

    if (latestRun.status === 'blocked') {
      return {
        label: 'Blocked',
        style: { background: '#fff7e6', color: '#9a6700' },
      };
    }

    if (latestRun.status === 'inconclusive') {
      return {
        label: 'Inconclusive',
        style: { background: '#f2f4f7', color: '#344054' },
      };
    }

    if (latestRun.status === 'suspicious') {
      return {
        label: 'Suspicious',
        style: { background: '#fef3c7', color: '#92400e' },
      };
    }

    return {
      label: latestRun.status,
      style: { background: '#fff3cd', color: '#8a6d3b' },
    };
  };

  const getExecutionStatusColor = (status: string): string => {
    if (status === 'passed') return '#1b5e20';
    if (status === 'failed') return '#b42318';
    if (status === 'blocked') return '#9a6700';
    if (status === 'inconclusive') return '#344054';
    if (status === 'suspicious') return '#92400e';
    return '#344054';
  };

  const getStepVerdictColor = (status: string): string => {
    if (status === 'passed') return '#1b5e20';
    if (status === 'failed') return '#b42318';
    if (status === 'blocked') return '#9a6700';
    if (status === 'inconclusive') return '#344054';
    if (status === 'suspicious') return '#92400e';
    return '#344054';
  };

  const jumpToLatestExecution = (testCaseId: string): void => {
    const latestRun = latestRunByTestCaseId[testCaseId];
    if (!latestRun) return;

    const runRow = document.getElementById(`execution-run-${latestRun.id}`);
    const fallbackAnchor = document.getElementById('executions-panel-anchor');
    const target = (runRow ?? fallbackAnchor) as HTMLElement | null;
    if (!target) return;

    // Open all parent detail sections so the target run is visible after scrolling.
    let currentParent = target.parentElement;
    while (currentParent) {
      if (currentParent.tagName === 'DETAILS') {
        (currentParent as HTMLDetailsElement).open = true;
      }
      currentParent = currentParent.parentElement;
    }

    target.scrollIntoView({ behavior: 'smooth', block: 'start' });

    setHighlightedRunId(latestRun.id);
    if (highlightTimerRef.current !== null) {
      window.clearTimeout(highlightTimerRef.current);
    }
    highlightTimerRef.current = window.setTimeout(() => {
      setHighlightedRunId(null);
      highlightTimerRef.current = null;
    }, 2200);
  };

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      {error ? <div style={{ padding: 12, background: '#fdecec', border: '1px solid #f4b1b1', borderRadius: 8 }}>{error}</div> : null}

      <Panel title="✦ AI Assist — Describe your requirement">
        <div style={{ display: 'grid', gap: 10 }}>
          <input
            type="password"
            value={aiApiKey}
            placeholder="Your OpenAI API key (used only for AI actions in this browser)"
            onChange={(e) => setAiApiKey(e.target.value)}
          />
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
          <input
            value={form.project_code}
            placeholder="Project code (e.g. APP)"
            required
            onChange={(e) => setForm({ ...form, project_code: e.target.value.toUpperCase().replace(/\s+/g, '') })}
          />
          <input value={form.title} placeholder="Requirement title" required onChange={(e) => setForm({ ...form, title: e.target.value })} />
          <textarea value={form.description} placeholder="Requirement description" rows={4} required onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <input
            value={form.target_url}
            placeholder="Target web URL (e.g. https://dev.educatifu.com/)"
            onChange={(e) => setForm({ ...form, target_url: e.target.value })}
          />
          <div style={{ display: 'flex', gap: 12 }}>
            <select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}>
              {priorities.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
            <select value={form.risk} onChange={(e) => setForm({ ...form, risk: e.target.value })}>
              {risks.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </div>
          <div style={{ display: 'grid', gap: 6 }}>
            <div>Platforms</div>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              {platformOptions.map((platform) => (
                <label key={platform} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <input
                    type="checkbox"
                    checked={selectedPlatforms.includes(platform)}
                    onChange={() => togglePlatform(platform)}
                  />
                  {platform}
                </label>
              ))}
            </div>
          </div>
          <textarea value={form.business_rules} placeholder="Business rules, one per line" rows={3} onChange={(e) => setForm({ ...form, business_rules: e.target.value })} />
          <button type="submit" disabled={busy === 'requirement'}>{busy === 'requirement' ? 'Creating...' : 'Create requirement'}</button>
        </form>
      </Panel>

      <div style={{ display: 'grid', gap: 16, gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))' }}>

        {/* ── Requirements ────────────────────────────────── */}
        <Panel title="Requirements">
          {requirements.length === 0 ? <p>No requirements yet.</p> : requirementsByProject.map((projectGroup) => (
            <details key={projectGroup.projectCode} style={{ marginBottom: 16, paddingBottom: 12, paddingLeft: 0, borderBottom: '1px solid #d9e1ec' }}>
              <summary style={{ cursor: 'pointer', listStylePosition: 'inside' }}>
                <strong>Project: {projectGroup.projectCode} ({projectGroup.items.length} requirement{projectGroup.items.length > 1 ? 's' : ''})</strong>
              </summary>
              <div style={{ marginLeft: 20, marginTop: 8 }}>
                {[...projectGroup.items].reverse().map((item) => (
                  <details key={item.id} style={{ marginBottom: 16, paddingBottom: 16, paddingLeft: 0, borderBottom: '1px solid #e3e8ef' }}>
                    <summary style={{ cursor: 'pointer', listStylePosition: 'inside' }}>
                      <strong>{item.title}</strong>
                    </summary>
                    <div style={{ marginLeft: 22, marginTop: 6 }}>
                      <div style={{ fontSize: 11, color: '#8a96a3', marginBottom: 4 }}>{item.id}</div>
                      <div style={{ fontSize: 11, color: '#0066cc', marginBottom: 4 }}>
                        Created: {formatDateTime(item.created_at)} {item.updated_at !== item.created_at && `| Updated: ${formatDateTime(item.updated_at)}`}
                      </div>
                      <div style={{ margin: '4px 0' }}>{item.description}</div>
                      {item.target_url ? (
                        <div style={{ margin: '4px 0', fontSize: 12 }}>
                          Target: <a href={item.target_url} target="_blank" rel="noreferrer">{item.target_url}</a>
                        </div>
                      ) : null}
                      <div>{item.platforms.join(', ')} | {item.priority} / {item.risk}</div>
                      <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                        <button onClick={() => generateTestCases(item.id)} disabled={busy === item.id}>
                          {busy === item.id ? 'Generating...' : 'Generate test cases'}
                        </button>
                        {userRole === 'admin' && (
                          <button onClick={() => deleteRequirement(item.id)} disabled={busy === `delete-req-${item.id}`}>
                            {busy === `delete-req-${item.id}` ? 'Deleting...' : 'Delete requirement'}
                          </button>
                        )}
                      </div>
                    </div>
                  </details>
                ))}
              </div>
            </details>
          ))}
        </Panel>

        {/* ── Test Cases — grouped by Project -> TC base -> versions ── */}
        <Panel title="Test Cases">
          <div style={{ marginBottom: 10, padding: 10, borderRadius: 8, background: '#f8fafc', border: '1px solid #e2e8f0' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
              <input
                type="checkbox"
                checked={executionHeadless}
                onChange={(event) => setExecutionHeadless(event.target.checked)}
              />
              Run web executions in headless mode
            </label>
            <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>
              Turn this off for headed mode when running locally with a display.
            </div>
          </div>
          {testCases.length === 0 ? <p>No test cases yet.</p> : testCasesByProject.map((projectGroup) => (
            <details key={projectGroup.projectCode} style={{ marginBottom: 20, paddingBottom: 12, paddingLeft: 0, borderBottom: '1px solid #d9e1ec' }}>
              <summary style={{ cursor: 'pointer', listStylePosition: 'inside' }}>
                <strong>Project: {projectGroup.projectCode} ({projectGroup.totalCases} test case{projectGroup.totalCases > 1 ? 's' : ''})</strong>
              </summary>

              <div style={{ marginLeft: 20, marginTop: 8 }}>
                {projectGroup.tcGroups.map((group) => {

                  return (
                    <details key={group.tcBase} style={{ marginBottom: 16, paddingBottom: 12, paddingLeft: 0, borderBottom: '1px solid #e3e8ef' }}>
                      <summary style={{ cursor: 'pointer', listStylePosition: 'inside' }}>
                        <span style={{ fontSize: 12, fontWeight: 600 }}>
                          {group.tcBase} ({group.versions.length} version{group.versions.length > 1 ? 's' : ''})
                        </span>
                      </summary>

                      <div style={{ marginLeft: 40 }}>
                        {group.versions.map((item) => {
                          const parentReq = requirementById[item.requirement_id];
                          const resultBadge = getTestCaseResultBadge(item.id);

                          return (
                          <div key={item.id} style={{ marginBottom: 16, paddingBottom: 16, borderBottom: '1px solid #e3e8ef' }}>
                            <div><strong>{testCaseVersionById[item.id] ?? 'TC-0000-v1'}</strong></div>
                            <div style={{ fontSize: 12, color: '#6f7c8a', marginBottom: 2 }}>
                              {item.title}
                              {parentReq ? ` - ${parentReq.title}` : ''}
                            </div>
                            <div style={{ fontSize: 11, marginBottom: 4 }}>
                              {parentReq ? (
                                <span style={{ background: '#e8f4fd', color: '#1565c0', borderRadius: 4, padding: '1px 6px' }}>
                                  {item.requirement_id}
                                </span>
                              ) : (
                                <span style={{ background: '#fff3cd', color: '#8a6d3b', borderRadius: 4, padding: '1px 6px' }}>
                                  Requirement not found
                                </span>
                              )}
                            </div>
                            <div style={{ fontSize: 11, color: '#0066cc', marginBottom: 4 }}>
                              Created: {formatDateTime(item.created_at)} {item.updated_at !== item.created_at && `| Updated: ${formatDateTime(item.updated_at)}`}
                            </div>
                            <div style={{ display: 'flex', gap: 6, alignItems: 'center', margin: '4px 0' }}>
                              <span>{item.platform} | {item.review_status}</span>
                              {latestRunByTestCaseId[item.id] ? (
                                <button
                                  type="button"
                                  onClick={() => jumpToLatestExecution(item.id)}
                                  title="Jump to latest execution"
                                  style={{
                                    ...resultBadge.style,
                                    fontSize: 11,
                                    padding: '1px 8px',
                                    borderRadius: 10,
                                    textTransform: 'capitalize',
                                    fontWeight: 600,
                                    border: 'none',
                                    cursor: 'pointer',
                                  }}
                                >
                                  {resultBadge.label}
                                </button>
                              ) : (
                                <span style={{ ...resultBadge.style, fontSize: 11, padding: '1px 8px', borderRadius: 10, textTransform: 'capitalize', fontWeight: 600 }}>
                                  {resultBadge.label}
                                </span>
                              )}
                              {item.metadata?.ai_generated ? <span style={{ fontSize: 11, background: '#e8f4fd', color: '#1565c0', padding: '1px 6px', borderRadius: 10 }}>AI</span> : null}
                            </div>
                            <div style={{ margin: '4px 0' }}>{item.objective}</div>
                            {typeof item.metadata?.target_url === 'string' && item.metadata.target_url ? (
                              <div style={{ margin: '4px 0', fontSize: 12 }}>
                                Target: <a href={item.metadata.target_url as string} target="_blank" rel="noreferrer">{item.metadata.target_url as string}</a>
                              </div>
                            ) : null}
                            <details style={{ marginTop: 6 }}>
                              <summary style={{ cursor: 'pointer', fontSize: 13 }}>Test steps ({item.steps.length})</summary>
                              <ul style={{ marginTop: 8, marginBottom: 0, paddingLeft: 18 }}>
                                {item.steps.map((step, index) => (
                                  <li key={`${item.id}-step-${index}`}>
                                    {step.action}:{step.target}
                                    {step.value ? ` (${step.value})` : ''}
                                  </li>
                                ))}
                              </ul>
                            </details>
                            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 6 }}>
                              {reviewStatuses.map((status) => (
                                <button key={status} onClick={() => reviewTestCase(item.id, status)} disabled={busy === item.id || item.review_status === status}>
                                  {status}
                                </button>
                              ))}
                              <button onClick={() => startExecution(item)} disabled={busy === `run-${item.id}` || item.review_status !== 'approved'}>
                                {busy === `run-${item.id}` ? 'Running...' : 'Start execution'}
                              </button>
                              {userRole === 'admin' && (
                                <button onClick={() => deleteTestCase(item)} disabled={busy === `delete-${item.id}`}>
                                  {busy === `delete-${item.id}` ? 'Deleting...' : 'Delete test case'}
                                </button>
                              )}
                            </div>
                          </div>
                          );
                        })}
                      </div>
                    </details>
                  );
                })}
              </div>
            </details>
          ))}
        </Panel>

        {/* ── Executions — grouped by test case ── */}
        <Panel title="Executions">
          <div id="executions-panel-anchor" />
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

                          {(() => {
                            const runsOrderedOldestToNewest = [...versionGroup.runs].sort(
                              (a, b) => new Date(a.started_at).getTime() - new Date(b.started_at).getTime(),
                            );
                            const executionOrderByRunId: Record<string, number> = {};
                            runsOrderedOldestToNewest.forEach((run, index) => {
                              executionOrderByRunId[run.id] = index + 1;
                            });

                            const runsNewestFirst = [...runsOrderedOldestToNewest].reverse();

                            return runsNewestFirst.map((item) => (
                            <div
                              id={`execution-run-${item.id}`}
                              key={item.id}
                              style={{
                                marginBottom: 14,
                                paddingBottom: 14,
                                borderBottom: highlightedRunId === item.id ? '2px solid #f79009' : '1px solid #e3e8ef',
                                background:
                                  highlightedRunId === item.id
                                    ? '#fff9e6'
                                    : item.status === 'failed'
                                      ? '#fff1f1'
                                      : item.status === 'blocked'
                                        ? '#fff8e1'
                                        : item.status === 'inconclusive'
                                          ? '#f8fafc'
                                          : item.status === 'suspicious'
                                            ? '#fff7e6'
                                        : 'transparent',
                                borderRadius: highlightedRunId === item.id ? 6 : 0,
                                transition: 'background 220ms ease, border-color 220ms ease',
                              }}
                            >
                              <div><strong>{getExecutionLabel(executionOrderByRunId[item.id] ?? 0)}</strong></div>
                              <div style={{ color: getExecutionStatusColor(item.status), fontWeight: 600 }}>
                                {item.status} | Confidence: {item.confidence_score.toFixed(2)}
                              </div>
                              <div style={{ fontSize: 12, color: '#475467', marginBottom: 2 }}>
                                Mode: {item.run_mode === 'headed' ? 'headed' : 'headless'}
                              </div>
                              <div style={{ fontSize: 11, color: '#0066cc', marginBottom: 4 }}>
                                Started: {formatDateTime(item.started_at)} {item.finished_at && `| Finished: ${formatDateTime(item.finished_at)}`}
                              </div>
                              <div style={{ margin: '4px 0', fontSize: 13 }}>{item.summary_reason}</div>
                              {userRole === 'admin' && (
                                <div style={{ margin: '4px 0' }}>
                                  <button onClick={() => deleteExecution(item)} disabled={busy === `delete-run-${item.id}`}>
                                    {busy === `delete-run-${item.id}` ? 'Deleting...' : 'Delete execution'}
                                  </button>
                                </div>
                              )}
                              <details>
                                <summary style={{ cursor: 'pointer', fontSize: 13 }}>Step details</summary>
                                <ul>
                                  {item.steps.map((step) => (
                                    <li
                                      key={`${item.id}-${step.step_number}`}
                                      style={{
                                        marginBottom: 8,
                                        color:
                                          step.verdict.status === 'failed'
                                            ? '#b42318'
                                            : step.verdict.status === 'blocked'
                                              ? '#9a6700'
                                              : step.verdict.status === 'inconclusive'
                                                ? '#344054'
                                                : step.verdict.status === 'suspicious'
                                                  ? '#92400e'
                                                  : undefined,
                                      }}
                                    >
                                      <div>
                                        {step.action} {'→'} <strong style={{ color: getStepVerdictColor(step.verdict.status) }}>{step.verdict.status}</strong>
                                      </div>
                                      <div
                                        style={{
                                          fontSize: 12,
                                          color:
                                            step.verdict.status === 'failed'
                                              ? '#b42318'
                                              : step.verdict.status === 'blocked'
                                                ? '#9a6700'
                                                : step.verdict.status === 'inconclusive'
                                                  ? '#344054'
                                                  : step.verdict.status === 'suspicious'
                                                    ? '#92400e'
                                                    : '#6f7c8a',
                                        }}
                                      >
                                        {step.verdict.status === 'failed' || step.verdict.status === 'blocked' || step.verdict.status === 'suspicious' || step.verdict.status === 'inconclusive'
                                          ? `Error: ${step.verdict.reason}`
                                          : step.verdict.reason}
                                      </div>
                                    </li>
                                  ))}
                                </ul>
                              </details>
                            </div>
                            ));
                          })()}
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
