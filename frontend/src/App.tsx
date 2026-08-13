import { useEffect, useMemo, useState, type FormEvent } from "react";
import {
  Activity, AlertTriangle, ArrowUpRight, BarChart3, Bell, Bolt, Bot, Braces, Check,
  ChevronDown, CircleAlert, Clock3, Code2, FileCode2, GitBranch, Github, KeyRound,
  LayoutDashboard, LoaderCircle, LogOut, Plus, RefreshCw, Search, Settings, ShieldAlert,
  Sparkles, Timer, TriangleAlert, Users, Wrench, X,
} from "lucide-react";
import { api, auth } from "./api";
import type { Analysis, AnalysisDetail, Finding, Repository, Severity } from "./types";

const severityOrder: Severity[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"];
const scoreLabels = [
  ["quality_score", "Code quality", Code2, "Measures maintainable, clear implementation."],
  ["security_score", "Security", ShieldAlert, "Vulnerabilities and unsafe code paths."],
  ["maintainability_score", "Maintainability", Wrench, "Debt, complexity, and change cost."],
  ["architecture_score", "Architecture", Braces, "Layering and boundary health."],
] as const;

function scoreTone(score: number | null) {
  if (score === null) return "neutral";
  if (score >= 85) return "good";
  if (score >= 65) return "warning";
  return "danger";
}

function ScoreCard({ label, score, Icon, hint }: { label: string; score: number | null; Icon: typeof Code2; hint: string }) {
  const progress = score ?? 0;
  return <article className="score-card">
    <div className="score-top"><span className="score-icon"><Icon size={17} /></span><span className={`score-value ${scoreTone(score)}`}>{score ?? "—"}</span></div>
    <div className="score-label">{label}</div>
    <div className="meter"><i className={scoreTone(score)} style={{ width: `${progress}%` }} /></div>
    <small>{score === null ? "Awaiting analysis" : hint}</small>
  </article>;
}

function SeverityBadge({ severity }: { severity: Severity }) {
  return <span className={`severity ${severity.toLowerCase()}`}>{severity}</span>;
}

function AuthGate({ onAuthenticated }: { onAuthenticated: () => void }) {
  const [register, setRegister] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault(); setPending(true); setError("");
    try { const response = await api.authenticate(email, password, register); auth.set(response.access_token); onAuthenticated(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Authentication failed"); }
    finally { setPending(false); }
  }
  return <main className="auth-shell">
    <section className="auth-hero">
      <div className="brand"><span className="brand-mark"><ShieldAlert size={21} /></span>CodeGuardian</div>
      <div className="hero-copy"><span className="eyebrow"><Sparkles size={15} /> AI-powered code intelligence</span><h1>Ship with confidence,<br /><em>not guesswork.</em></h1><p>Find vulnerabilities, architectural drift, and risky changes before they reach production.</p></div>
      <div className="hero-orbit"><span className="orbit-line" /><span className="orbit-core"><Bot size={40} /></span><span className="orbit-tag tag-one">Security</span><span className="orbit-tag tag-two">Quality</span><span className="orbit-tag tag-three">Architecture</span></div>
      <small className="secure-note"><KeyRound size={14} /> Encrypted connections · Your code stays under your control</small>
    </section>
    <section className="auth-panel"><div className="auth-card">
      <div className="auth-heading"><span className="eyebrow dark">GET STARTED</span><h2>{register ? "Create your workspace" : "Welcome back"}</h2><p>{register ? "Start your first repository analysis in minutes." : "Sign in to your engineering intelligence."}</p></div>
      <form onSubmit={submit}><label>Work email<input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@company.com" required /></label><label>Password<input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="At least 12 characters" minLength={12} required /></label>{error && <div className="form-error"><CircleAlert size={15} />{error}</div>}<button className="primary full" disabled={pending}>{pending && <LoaderCircle className="spin" size={17} />}{register ? "Create workspace" : "Sign in"}<ArrowUpRight size={17} /></button></form>
      <p className="switch-auth">{register ? "Already have an account?" : "New to CodeGuardian?"} <button onClick={() => setRegister(!register)}>{register ? "Sign in" : "Create an account"}</button></p>
    </div></section>
  </main>;
}

function ConnectRepository({ onClose, onConnected }: { onClose: () => void; onConnected: (repository: Repository) => void }) {
  const [owner, setOwner] = useState(""); const [name, setName] = useState(""); const [branch, setBranch] = useState("main"); const [error, setError] = useState(""); const [pending, setPending] = useState(false);
  async function submit(event: FormEvent) { event.preventDefault(); setPending(true); setError(""); try { onConnected(await api.createRepository(owner, name, branch)); } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not connect repository"); } finally { setPending(false); } }
  return <div className="modal-backdrop"><form className="modal" onSubmit={submit}><div className="modal-title"><div><span className="eyebrow dark">GITHUB INTEGRATION</span><h2>Connect a repository</h2></div><button type="button" className="icon-button" onClick={onClose}><X size={20} /></button></div><p>Use an organization and repository that your GitHub token or app installation can access.</p><div className="repo-inputs"><label>Owner or organization<input value={owner} onChange={e => setOwner(e.target.value)} placeholder="acme" required /></label><label>Repository<input value={name} onChange={e => setName(e.target.value)} placeholder="checkout-service" required /></label></div><label>Default branch<input value={branch} onChange={e => setBranch(e.target.value)} placeholder="main" required /></label>{error && <div className="form-error"><CircleAlert size={15} />{error}</div>}<div className="modal-actions"><button type="button" className="text-button" onClick={onClose}>Cancel</button><button className="primary" disabled={pending}>{pending && <LoaderCircle className="spin" size={16} />}<Github size={16} />Connect repository</button></div></form></div>;
}

function FindingsList({ findings, active, onSelect }: { findings: Finding[]; active: string | null; onSelect: (finding: Finding) => void }) {
  return <div className="findings-list">{findings.length === 0 ? <div className="empty-findings"><Check size={26} /><strong>No findings in this scope</strong><span>This is a good opportunity to inspect a different category.</span></div> : findings.map(finding => <button key={finding.id} className={`finding-row ${active === finding.id ? "active" : ""}`} onClick={() => onSelect(finding)}><div className="finding-main"><SeverityBadge severity={finding.severity} /><strong>{finding.title}</strong><span><FileCode2 size={14} />{finding.file_path}:{finding.start_line}</span></div><div className="finding-meta"><span>{finding.confidence}% confidence</span><ChevronDown size={17} /></div></button>)}</div>;
}

function FindingDetail({ finding, onClose, onPublish }: { finding: Finding; onClose: () => void; onPublish: (finding: Finding) => void }) {
  return <aside className="finding-detail"><div className="detail-head"><div><SeverityBadge severity={finding.severity} /><span className="rule-id">{finding.rule_id}</span></div><button className="icon-button" onClick={onClose}><X size={18} /></button></div><h3>{finding.title}</h3><p>{finding.explanation}</p><div className="code-location"><div><FileCode2 size={15} />{finding.file_path}<span>Ln {finding.start_line}</span></div><pre><code><span className="line-number">{finding.start_line}</span>{finding.code_snippet || "Source context unavailable"}</code></pre></div><section className="fix-card"><div><Sparkles size={16} /><strong>Suggested fix</strong></div><p>{finding.suggested_fix}</p></section><div className="detail-footer"><span><Activity size={14} /> {finding.confidence}% confidence</span><button className="secondary" onClick={() => onPublish(finding)}><Github size={15} />Add to PR review</button></div></aside>;
}

function Dashboard() {
  const [repositories, setRepositories] = useState<Repository[]>([]); const [repo, setRepo] = useState<Repository | null>(null); const [analyses, setAnalyses] = useState<Analysis[]>([]); const [report, setReport] = useState<AnalysisDetail | null>(null); const [branch, setBranch] = useState("main"); const [branches, setBranches] = useState<string[]>([]); const [filter, setFilter] = useState<Severity | "ALL">("ALL"); const [activeFinding, setActiveFinding] = useState<Finding | null>(null); const [connectOpen, setConnectOpen] = useState(false); const [busy, setBusy] = useState(false); const [notice, setNotice] = useState("");
  const loadAnalyses = async (current: Repository) => { const list = await api.analyses(current.id); setAnalyses(list); if (list[0]) setReport(await api.analysis(list[0].id)); else setReport(null); };
  const chooseRepo = async (current: Repository) => { setRepo(current); setBranch(current.default_branch); setActiveFinding(null); try { setBranches(await api.branches(current.id)); } catch { setBranches([current.default_branch]); } try { await loadAnalyses(current); } catch (reason) { setNotice(reason instanceof Error ? reason.message : "Could not load analyses"); } };
  useEffect(() => { api.repositories().then(items => { setRepositories(items); if (items[0]) void chooseRepo(items[0]); }).catch(reason => { if (reason instanceof Error) setNotice(reason.message); }); }, []);
  useEffect(() => { if (!report || !["QUEUED", "RUNNING"].includes(report.status)) return; const id = window.setInterval(() => { api.analysis(report.id).then(setReport).catch(() => undefined); }, 3000); return () => window.clearInterval(id); }, [report?.id, report?.status]);
  const findings = useMemo(() => report?.findings.filter(item => filter === "ALL" || item.severity === filter) || [], [report, filter]);
  const counts = useMemo(() => severityOrder.reduce((all, severity) => ({ ...all, [severity]: report?.findings.filter(item => item.severity === severity).length || 0 }), {} as Record<Severity, number>), [report]);
  async function runAnalysis() { if (!repo) return; setBusy(true); setNotice(""); try { const queued = await api.trigger(repo.id, branch); setAnalyses([queued, ...analyses]); setReport(await api.analysis(queued.id).catch(() => ({ ...queued, findings: [] }))); } catch (reason) { setNotice(reason instanceof Error ? reason.message : "Could not queue analysis"); } finally { setBusy(false); } }
  async function publish(finding: Finding) { if (!report) return; const pull = window.prompt("Pull request number to comment on:"); if (!pull || !/^\d+$/.test(pull)) return; try { const result = await api.publishReview(report.id, Number(pull), [finding.id]); setNotice(`Published ${result.submitted} GitHub review comment.`); } catch (reason) { setNotice(reason instanceof Error ? reason.message : "Could not publish review"); } }
  return <div className="app-shell"><aside className="sidebar"><div className="brand"><span className="brand-mark"><ShieldAlert size={20} /></span>CodeGuardian</div><nav><a className="nav-item active"><LayoutDashboard size={18} />Overview</a><a className="nav-item"><Activity size={18} />Analysis</a><a className="nav-item"><GitBranch size={18} />Pull requests<span className="nav-badge">New</span></a><a className="nav-item"><BarChart3 size={18} />Insights</a><a className="nav-item"><Settings size={18} />Settings</a></nav><div className="sidebar-footer"><div className="plan-card"><span><Bolt size={15} />TEAM PLAN</span><strong>Proactive security</strong><small>18 analysis credits left</small><div><i style={{ width: "58%" }} /></div></div><button className="user-pill" onClick={() => { auth.clear(); window.location.reload(); }}><span className="avatar">CG</span><span><strong>Workspace</strong><small>Sign out</small></span><LogOut size={16} /></button></div></aside>
    <main className="dashboard"><header className="topbar"><div className="breadcrumbs"><span>Repositories</span><ChevronDown size={15} />{repo ? <strong>{repo.github_owner}/{repo.github_name}</strong> : <strong>Choose a repository</strong>}</div><div className="top-actions"><button className="icon-button"><Search size={18} /></button><button className="icon-button bell"><Bell size={18} /><i /></button><button className="secondary" onClick={() => setConnectOpen(true)}><Plus size={16} />Repository</button></div></header>
      {notice && <div className="notice"><CircleAlert size={16} />{notice}<button onClick={() => setNotice("")}><X size={15} /></button></div>}
      {!repo ? <section className="onboarding"><div className="empty-orb"><Github size={38} /></div><span className="eyebrow dark">YOUR FIRST REPOSITORY</span><h1>Turn every pull request into a stronger one.</h1><p>Connect a GitHub repository to start scanning its branches for code risks, architecture drift, and hidden debt.</p><button className="primary" onClick={() => setConnectOpen(true)}><Github size={17} />Connect GitHub repository</button></section> : <>
        <section className="workspace-header"><div><div className="repo-title"><span className="repo-icon"><Github size={19} /></span><h1>{repo.github_name}</h1><span className="private-tag">PRIVATE</span></div><p>{repo.github_owner} · Last analysis {report?.created_at ? new Date(report.created_at).toLocaleString() : "not run yet"}</p></div><div className="analysis-controls"><div className="branch-select"><GitBranch size={16} /><select value={branch} onChange={e => setBranch(e.target.value)}>{[...new Set([branch, ...branches])].map(item => <option key={item}>{item}</option>)}</select><ChevronDown size={15} /></div><button className="primary" onClick={runAnalysis} disabled={busy}>{busy ? <LoaderCircle className="spin" size={17} /> : <RefreshCw size={16} />}Run analysis</button></div></section>
        <section className="score-grid">{scoreLabels.map(([key, label, Icon, hint]) => <ScoreCard key={key} label={label} score={report?.[key] ?? null} Icon={Icon} hint={hint} />)}<article className="debt-card"><div><span className="score-icon purple"><Timer size={17} /></span><span className="debt-value">{report?.technical_debt_minutes ?? "—"}</span><small>min</small></div><strong>Technical debt</strong><p>{report ? "Estimated remediation effort" : "Awaiting analysis"}</p></article></section>
        <section className="analytics-grid"><article className="panel trends-panel"><div className="panel-head"><div><span className="eyebrow dark">REPOSITORY HEALTH</span><h2>Issue trend</h2></div><button className="text-button">Last 30 days <ChevronDown size={14} /></button></div><div className="trend-key"><span><i className="critical-dot" />Critical & high</span><span><i className="quality-dot" />Quality</span></div><div className="chart"><div className="grid-line one" /><div className="grid-line two" /><div className="grid-line three" /><svg viewBox="0 0 600 160" preserveAspectRatio="none" aria-label="Issue trend chart"><path className="area" d="M0,126 C43,120 52,93 95,100 S142,75 180,86 S230,112 270,87 S326,55 360,70 S406,86 450,50 S518,73 600,27 L600,160 L0,160Z" /><path className="line-main" d="M0,126 C43,120 52,93 95,100 S142,75 180,86 S230,112 270,87 S326,55 360,70 S406,86 450,50 S518,73 600,27" /><path className="line-sub" d="M0,139 C62,124 92,130 135,117 S200,132 240,122 S315,108 355,116 S405,104 450,99 S520,87 600,72" /></svg><div className="chart-labels"><span>Jul 11</span><span>Jul 18</span><span>Jul 25</span><span>Aug 1</span><span>Today</span></div></div></article><article className="panel distribution"><div className="panel-head"><div><span className="eyebrow dark">FINDINGS</span><h2>Severity distribution</h2></div><CircleAlert size={19} /></div><div className="severity-chart"><div className="donut"><div><strong>{report?.findings.length ?? 0}</strong><small>open</small></div></div><div className="legend">{severityOrder.slice(0, 4).map(severity => <span key={severity}><i className={severity.toLowerCase()} />{severity}<strong>{counts[severity]}</strong></span>)}</div></div></article></section>
        <section className="findings-section"><div className="section-head"><div><span className="eyebrow dark">ANALYSIS REPORT</span><h2>Findings <span>{report?.findings.length ?? 0}</span></h2></div>{report && <div className="report-status"><span className={`status-dot ${report.status.toLowerCase()}`} />{report.status === "COMPLETED" ? `Commit ${report.commit_sha?.slice(0, 7) || "local"}` : report.status}</div>}</div><div className="finding-toolbar"><div className="severity-tabs"><button className={filter === "ALL" ? "selected" : ""} onClick={() => setFilter("ALL")}>All <span>{report?.findings.length ?? 0}</span></button>{severityOrder.slice(0, 4).map(severity => <button key={severity} className={filter === severity ? "selected" : ""} onClick={() => setFilter(severity)}>{severity[0] + severity.slice(1).toLowerCase()} <span>{counts[severity]}</span></button>)}</div><button className="secondary"><Users size={15} />Assign review</button></div><FindingsList findings={findings} active={activeFinding?.id ?? null} onSelect={setActiveFinding} /></section>
      </>}
    </main>{activeFinding && <FindingDetail finding={activeFinding} onClose={() => setActiveFinding(null)} onPublish={publish} />}{connectOpen && <ConnectRepository onClose={() => setConnectOpen(false)} onConnected={created => { setConnectOpen(false); setRepositories([created, ...repositories]); void chooseRepo(created); }} />}
  </div>;
}

export default function App() { const [loggedIn, setLoggedIn] = useState(auth.loggedIn); return loggedIn ? <Dashboard /> : <AuthGate onAuthenticated={() => setLoggedIn(true)} />; }

