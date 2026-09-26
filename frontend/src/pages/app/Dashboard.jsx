import { Link, useOutletContext } from 'react-router-dom'
import { getBom, listRepos } from '../../api/bomwatcher'
import Icon from '../../components/Icon'
import { Alert, EmptyState, PageLoader, StatusBadge } from '../../components/ui'
import { licenseOf, needsLicenseReview, property, summarize } from '../../lib/bom'
import { useAsync } from '../../lib/hooks'
import { timeAgo } from '../../lib/format'

const IN_PROGRESS = new Set(['pr_open', 'scanning', 'pending'])

async function loadDashboard() {
  const repos = await listRepos()
  const tracked = repos.filter((r) => r.status !== 'not_enabled')
  const scanned = tracked.filter((r) => r.last_scan_at)
  const boms = await Promise.all(scanned.map((r) => getBom(r.id).then((bom) => ({ repo: r, bom })).catch(() => null)))
  return { tracked, boms: boms.filter(Boolean) }
}

function Onboarding({ installation, tracked }) {
  const steps = [
    { done: true, label: 'Create your account' },
    { done: !!installation, label: 'Connect GitHub', to: '/app/github' },
    { done: tracked.length > 0, label: 'Pick repos to scan', to: '/app/repos' },
    { done: tracked.some((r) => r.pr?.merged), label: 'Merge the workflow PR on GitHub', to: '/app/repos' },
    { done: tracked.some((r) => r.last_scan_at), label: 'Get your first AI-BOM' },
  ]
  const next = steps.find((s) => !s.done)
  if (!next) return null
  const doneCount = steps.filter((s) => s.done).length
  return (
    <div className="card onboarding">
      <div className="onboarding-head">
        <div>
          <h3 className="card-title">Get set up</h3>
          <p className="muted small">
            {doneCount} of {steps.length} done
          </p>
        </div>
        {next.to && (
          <Link to={next.to} className="btn btn-primary">
            {next.label} <Icon name="arrowRight" size={14} />
          </Link>
        )}
      </div>
      <ol className="onboarding-steps">
        {steps.map((s) => (
          <li key={s.label} className={s.done ? 'done' : s === next ? 'current' : ''}>
            <span className="onb-dot">{s.done && <Icon name="check" size={12} strokeWidth={3} />}</span>
            {s.label}
          </li>
        ))}
      </ol>
    </div>
  )
}

function Stat({ icon, label, value, hint, tone }) {
  return (
    <div className={`card stat ${tone ? `stat-${tone}` : ''}`}>
      <div className="stat-label">
        <Icon name={icon} size={15} /> {label}
      </div>
      <div className="stat-value">{value}</div>
      {hint && <div className="stat-hint">{hint}</div>}
    </div>
  )
}

export default function Dashboard() {
  const { installation } = useOutletContext()
  const { data, loading, error } = useAsync(
    () => (installation ? loadDashboard() : Promise.resolve({ tracked: [], boms: [] })),
    installation?.id ?? null,
    { pollWhile: (d) => d?.tracked.some((r) => IN_PROGRESS.has(r.status)), interval: 4000 },
  )

  if (loading && !data) return <PageLoader />

  const tracked = data?.tracked ?? []
  const boms = data?.boms ?? []
  const summaries = boms.map(({ repo, bom }) => ({ repo, s: summarize(bom) }))
  const totalLibs = summaries.reduce((n, { s }) => n + s.libraries.length, 0)
  const totalReview = summaries.reduce((n, { s }) => n + s.reviewCount, 0)

  const modelMap = new Map()
  for (const { repo, s } of summaries) {
    for (const m of s.models) {
      const entry = modelMap.get(m.name) ?? { model: m, repos: [] }
      entry.repos.push(repo)
      modelMap.set(m.name, entry)
    }
  }
  const models = [...modelMap.values()].sort((a, b) => b.repos.length - a.repos.length)

  const flagged = boms.flatMap(({ repo, bom }) =>
    (bom.components ?? []).filter((c) => needsLicenseReview(licenseOf(c))).map((c) => ({ repo, c })),
  )

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Dashboard</h1>
          <p className="muted">Your AI and dependency inventory across every scanned repo.</p>
        </div>
        {installation && (
          <Link to="/app/repos" className="btn btn-secondary">
            <Icon name="repo" size={16} /> Manage repos
          </Link>
        )}
      </div>

      {error && <Alert>{error.message}</Alert>}

      <Onboarding installation={installation} tracked={tracked} />

      <div className="stats">
        <Stat icon="repo" label="Repos scanned" value={boms.length} hint={`${tracked.length} tracked`} />
        <Stat icon="package" label="Libraries" value={totalLibs} hint="across all BOMs" />
        <Stat icon="cpu" label="AI models" value={models.length} hint="distinct models" />
        <Stat icon="shield" label="License flags" value={totalReview} hint="copyleft or non-commercial" tone={totalReview ? 'warn' : undefined} />
      </div>

      <div className="grid-2">
        <div className="card flush">
          <div className="card-head">
            <h3 className="card-title">Tracked repositories</h3>
            <Link to="/app/repos" className="link-small">
              View all <Icon name="arrowRight" size={12} />
            </Link>
          </div>
          {tracked.length === 0 ? (
            <EmptyState icon="repo" title="No repos tracked yet" action={installation ? <Link className="btn btn-primary" to="/app/repos">Pick repos</Link> : <Link className="btn btn-primary" to="/app/github">Connect GitHub</Link>}>
              Pick repositories and BOMWatcher will open a PR adding the scan workflow.
            </EmptyState>
          ) : (
            <ul className="mini-list">
              {tracked.map((r) => (
                <li key={r.id}>
                  <Link to={`/app/repos/${r.id}`} className="mini-row">
                    <div>
                      <div className="strong">{r.name}</div>
                      <div className="muted small">
                        {r.last_scan_at ? `Scanned ${timeAgo(r.last_scan_at)}` : r.pr && !r.pr.merged ? `PR #${r.pr.number} opened ${timeAgo(r.pr.opened_at)}` : 'Waiting for scan'}
                      </div>
                    </div>
                    <StatusBadge status={r.status} />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card flush">
          <div className="card-head">
            <h3 className="card-title">AI models in use</h3>
          </div>
          {models.length === 0 ? (
            <EmptyState icon="cpu" title="No models detected yet">
              Models show up here once a scan finds SDK calls or model loads.
            </EmptyState>
          ) : (
            <ul className="mini-list">
              {models.map(({ model, repos }) => (
                <li key={model.name} className="mini-row">
                  <div>
                    <div className="strong mono">{model.name}</div>
                    <div className="muted small">
                      {model.supplier?.name} · {property(model, 'bomwatcher:hosting')} · {model.modelCard?.modelParameters?.task}
                    </div>
                  </div>
                  <span className="chip" title={repos.map((r) => r.name).join(', ')}>
                    {repos.length} repo{repos.length === 1 ? '' : 's'}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {flagged.length > 0 && (
        <div className="card flush">
          <div className="card-head">
            <h3 className="card-title">
              <Icon name="alert" size={16} className="warn-text" /> Licenses to review
            </h3>
          </div>
          <table className="table">
            <thead>
              <tr>
                <th>Component</th>
                <th>License</th>
                <th>Repository</th>
              </tr>
            </thead>
            <tbody>
              {flagged.map(({ repo, c }) => (
                <tr key={`${repo.id}-${c['bom-ref']}`}>
                  <td className="mono">
                    {c.name}
                    {c.version && <span className="muted">@{c.version}</span>}
                  </td>
                  <td>
                    <span className="badge badge-warn">{licenseOf(c)}</span>
                  </td>
                  <td>
                    <Link to={`/app/repos/${repo.id}`}>{repo.name}</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
