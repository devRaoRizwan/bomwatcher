import { useMemo, useState } from 'react'
import { Link, useNavigate, useOutletContext, useParams } from 'react-router-dom'
import { disableRepo, getBom, getRepo, rescan } from '../../api/bomwatcher'
import Icon from '../../components/Icon'
import { Alert, Button, EmptyState, Language, PageLoader, StatusBadge } from '../../components/ui'
import { downloadJson, ecosystemOf, isModel, licenseOf, needsLicenseReview, property, summarize } from '../../lib/bom'
import { useAsync } from '../../lib/hooks'
import { duration, formatDate, timeAgo } from '../../lib/format'

const TABS = [
  ['overview', 'Overview'],
  ['components', 'Components'],
  ['models', 'AI models'],
  ['services', 'Services'],
  ['scans', 'Scan history'],
  ['raw', 'Raw JSON'],
]

function Progress({ repo }) {
  const steps = [
    { key: 'pr', label: 'Workflow PR opened', done: !!repo.pr },
    { key: 'merge', label: 'PR merged', done: !!repo.pr?.merged },
    { key: 'scan', label: 'Scan running on GitHub Actions', done: repo.status === 'scanned', active: repo.status === 'scanning' },
    { key: 'bom', label: 'BOM ready', done: repo.status === 'scanned' },
  ]
  return (
    <div className="card">
      <ol className="progress">
        {steps.map((s) => (
          <li key={s.key} className={s.done ? 'done' : s.active ? 'active' : ''}>
            <span className="progress-dot">{s.done ? <Icon name="check" size={12} strokeWidth={3} /> : s.active && <span className="pulse-dot" />}</span>
            <span>{s.label}</span>
          </li>
        ))}
      </ol>
      {repo.status === 'pr_open' && (
        <div className="progress-help">
          <p>
            BOMWatcher opened <strong>PR #{repo.pr.number}</strong> adding <code>.github/workflows/bomwatcher-scan.yml</code>.
            Review and merge it, and the first scan starts on your runners.
          </p>
          <a href={repo.pr.url} target="_blank" rel="noreferrer" className="btn btn-primary">
            Review PR on GitHub <Icon name="external" size={14} />
          </a>
        </div>
      )}
      {repo.status === 'scanning' && <p className="progress-help muted">The workflow is running. This page updates when the BOM artifact arrives.</p>}
    </div>
  )
}

function BarList({ items, total }) {
  return (
    <ul className="bar-list">
      {items.map(([label, n]) => (
        <li key={label}>
          <div className="bar-label">
            <span>{label}</span>
            <span className="mono muted">{n}</span>
          </div>
          <div className="meter">
            <div className="meter-fill" style={{ width: `${(n / total) * 100}%` }} />
          </div>
        </li>
      ))}
    </ul>
  )
}

function Overview({ s }) {
  return (
    <>
      <div className="stats">
        <div className="card stat">
          <div className="stat-label">
            <Icon name="package" size={15} /> Libraries
          </div>
          <div className="stat-value">{s.libraries.length}</div>
          <div className="stat-hint">
            {s.direct} direct · {s.libraries.length - s.direct} transitive
          </div>
        </div>
        <div className="card stat">
          <div className="stat-label">
            <Icon name="cpu" size={15} /> AI models
          </div>
          <div className="stat-value">{s.models.length}</div>
          <div className="stat-hint">{s.providers.map(([p]) => p).join(', ') || 'none detected'}</div>
        </div>
        <div className="card stat">
          <div className="stat-label">
            <Icon name="cloud" size={15} /> AI services
          </div>
          <div className="stat-value">{s.services.length}</div>
          <div className="stat-hint">external APIs called</div>
        </div>
        <div className={`card stat ${s.reviewCount ? 'stat-warn' : ''}`}>
          <div className="stat-label">
            <Icon name="shield" size={15} /> License flags
          </div>
          <div className="stat-value">{s.reviewCount}</div>
          <div className="stat-hint">copyleft or non-commercial</div>
        </div>
      </div>
      <div className="grid-2">
        <div className="card">
          <h3 className="card-title">Ecosystems</h3>
          {s.ecosystems.length ? <BarList items={s.ecosystems} total={s.libraries.length} /> : <p className="muted">No libraries found.</p>}
        </div>
        <div className="card">
          <h3 className="card-title">Licenses</h3>
          {s.licenses.length ? <BarList items={s.licenses} total={s.licenses.reduce((n, [, c]) => n + c, 0)} /> : <p className="muted">No license data.</p>}
        </div>
      </div>
    </>
  )
}

function Components({ bom }) {
  const [q, setQ] = useState('')
  const [type, setType] = useState('all')
  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase()
    return bom.components.filter((c) => {
      if (type === 'library' && c.type !== 'library') return false
      if (type === 'model' && !isModel(c)) return false
      if (type === 'review' && !needsLicenseReview(licenseOf(c))) return false
      return !needle || c.name.toLowerCase().includes(needle) || c.purl?.toLowerCase().includes(needle)
    })
  }, [bom, q, type])

  return (
    <div className="card flush">
      <div className="toolbar in-card">
        <div className="search">
          <Icon name="search" size={16} />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter by name or purl" aria-label="Filter components" />
        </div>
        <select value={type} onChange={(e) => setType(e.target.value)} aria-label="Component type">
          <option value="all">All types</option>
          <option value="library">Libraries</option>
          <option value="model">AI models</option>
          <option value="review">License flags</option>
        </select>
      </div>
      {rows.length === 0 ? (
        <EmptyState icon="search" title="No components match" />
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Version</th>
                <th>Type</th>
                <th>Ecosystem</th>
                <th>Scope</th>
                <th>License</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((c) => {
                const lic = licenseOf(c)
                return (
                  <tr key={c['bom-ref']}>
                    <td>
                      <div className="mono strong">{c.name}</div>
                      {c.purl && <div className="muted tiny mono">{c.purl}</div>}
                    </td>
                    <td className="mono">{c.version ?? '—'}</td>
                    <td>
                      <span className={`chip ${isModel(c) ? 'chip-accent' : ''}`}>{isModel(c) ? 'model' : c.type}</span>
                    </td>
                    <td>{ecosystemOf(c) ?? c.supplier?.name ?? '—'}</td>
                    <td className="muted">{isModel(c) ? '—' : c.scope === 'optional' ? 'transitive' : 'direct'}</td>
                    <td>{lic ? <span className={needsLicenseReview(lic) ? 'badge badge-warn' : 'mono small'}>{lic}</span> : <span className="muted">—</span>}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function Models({ models }) {
  if (!models.length) {
    return (
      <div className="card">
        <EmptyState icon="cpu" title="No AI models detected">
          The scan didn't find SDK calls to model providers or local model loads in this repo.
        </EmptyState>
      </div>
    )
  }
  return (
    <div className="model-grid">
      {models.map((m) => (
        <div key={m['bom-ref']} className="card model-card">
          <div className="model-head">
            <div className="feature-icon">
              <Icon name="cpu" size={18} />
            </div>
            <div>
              <div className="mono strong">{m.name}</div>
              <div className="muted small">{m.supplier?.name}</div>
            </div>
          </div>
          <dl className="kv">
            <dt>Task</dt>
            <dd>{m.modelCard?.modelParameters?.task ?? '—'}</dd>
            <dt>Hosting</dt>
            <dd>{property(m, 'bomwatcher:hosting') ?? '—'}</dd>
            <dt>Detected via</dt>
            <dd>{property(m, 'bomwatcher:detectedVia') ?? '—'}</dd>
            <dt>License</dt>
            <dd>{licenseOf(m) ? <span className={needsLicenseReview(licenseOf(m)) ? 'badge badge-warn' : ''}>{licenseOf(m)}</span> : 'Provider terms'}</dd>
          </dl>
        </div>
      ))}
    </div>
  )
}

function Services({ services }) {
  if (!services.length) {
    return (
      <div className="card">
        <EmptyState icon="cloud" title="No external AI services">
          This repo doesn't call any hosted AI APIs that the scan could detect.
        </EmptyState>
      </div>
    )
  }
  return (
    <div className="card flush">
      <table className="table">
        <thead>
          <tr>
            <th>Service</th>
            <th>Provider</th>
            <th>Endpoints</th>
          </tr>
        </thead>
        <tbody>
          {services.map((s) => (
            <tr key={s['bom-ref']}>
              <td className="strong">{s.name}</td>
              <td>{s.provider?.name ?? '—'}</td>
              <td className="mono small">{s.endpoints?.join(', ')}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function Scans({ repo }) {
  if (!repo.scans.length) {
    return (
      <div className="card">
        <EmptyState icon="play" title="No scans yet">
          Scans appear here once the workflow PR is merged.
        </EmptyState>
      </div>
    )
  }
  return (
    <div className="card flush">
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Run</th>
              <th>Status</th>
              <th>Trigger</th>
              <th>Commit</th>
              <th>Started</th>
              <th>Duration</th>
              <th>Components</th>
            </tr>
          </thead>
          <tbody>
            {repo.scans.map((s) => (
              <tr key={s.id}>
                <td className="mono">
                  {s.run_url ? (
                    <a href={s.run_url} target="_blank" rel="noreferrer">
                      {s.id}
                    </a>
                  ) : (
                    s.id
                  )}
                </td>
                <td>
                  <StatusBadge status={s.status} />
                </td>
                <td className="muted">{s.trigger}</td>
                <td className="mono">{s.commit_sha.slice(0, 7)}</td>
                <td title={formatDate(s.started_at)}>{timeAgo(s.started_at)}</td>
                <td>{duration(s.started_at, s.finished_at)}</td>
                <td title={s.error ?? undefined}>{s.counts ? `${s.counts.libraries} libs · ${s.counts.models} models` : s.error ? <span className="muted">{s.error}</span> : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default function RepoDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { refresh } = useOutletContext()
  const [tab, setTab] = useState('overview')
  const [busy, setBusy] = useState(null)
  const [error, setError] = useState(null)

  const { data, loading, error: loadError, reload } = useAsync(
    async () => {
      const repo = await getRepo(id)
      const bom = repo.last_scan_at ? await getBom(id).catch(() => null) : null
      return { repo, bom }
    },
    id,
    { pollWhile: (d) => d && ['pr_open', 'scanning', 'pending'].includes(d.repo.status) },
  )

  if (loading && !data) return <PageLoader />
  if (loadError && !data) {
    return (
      <div className="card">
        <EmptyState icon="alert" title="Couldn't load repository" action={<Link to="/app/repos" className="btn btn-secondary">Back to repositories</Link>}>
          {loadError.message}
        </EmptyState>
      </div>
    )
  }

  const { repo, bom } = data
  const s = bom ? summarize(bom) : null

  const onRescan = async () => {
    setBusy('rescan')
    setError(null)
    try {
      await rescan(id)
      await reload(true)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(null)
    }
  }

  const onDisable = async () => {
    if (!confirm(`Stop tracking ${repo.name}? This frees a trial slot. Remove the workflow file from the repo yourself if you no longer want it to run.`)) return
    setBusy('disable')
    try {
      await disableRepo(id)
      await refresh()
      navigate('/app/repos')
    } catch (e) {
      setError(e.message)
      setBusy(null)
    }
  }

  return (
    <>
      <Link to="/app/repos" className="back-link">
        <Icon name="arrowLeft" size={14} /> Repositories
      </Link>

      <div className="page-head">
        <div>
          <h1 className="repo-title">
            {repo.full_name}
            <StatusBadge status={repo.status} />
          </h1>
          {repo.description && <p className="muted">{repo.description}</p>}
          <div className="repo-meta">
            <Language name={repo.language} />
            <span>
              <Icon name={repo.private ? 'lock' : 'globe'} size={12} /> {repo.private ? 'Private' : 'Public'}
            </span>
            <span>Branch {repo.default_branch}</span>
            {repo.last_scan_at && <span>Last scan {timeAgo(repo.last_scan_at)}</span>}
          </div>
        </div>
        <div className="row-actions">
          {bom && (
            <Button variant="secondary" icon="download" onClick={() => downloadJson(bom, `${repo.name}.cdx.json`)}>
              Download BOM
            </Button>
          )}
          {repo.pr?.merged && (
            <Button variant="secondary" icon="refresh" onClick={onRescan} loading={busy === 'rescan'} disabled={repo.status === 'scanning'}>
              Re-scan
            </Button>
          )}
          <Button variant="danger-ghost" onClick={onDisable} loading={busy === 'disable'}>
            Stop tracking
          </Button>
        </div>
      </div>

      {error && <Alert onClose={() => setError(null)}>{error}</Alert>}

      {repo.status === 'failed' && (
        <Alert>
          The last scan failed{repo.scans[0]?.error ? `: ${repo.scans[0].error}` : ''}. Check the workflow run on GitHub, then re-scan.
        </Alert>
      )}
      {!['scanned', 'failed'].includes(repo.status) && <Progress repo={repo} />}

      {s && (
        <>
          <div className="tabs" role="tablist">
            {TABS.map(([k, label]) => (
              <button key={k} role="tab" aria-selected={tab === k} className={tab === k ? 'active' : ''} onClick={() => setTab(k)}>
                {label}
                {k === 'components' && <span className="tab-count">{bom.components.length}</span>}
                {k === 'models' && <span className="tab-count">{s.models.length}</span>}
              </button>
            ))}
          </div>
          {tab === 'overview' && <Overview s={s} />}
          {tab === 'components' && <Components bom={bom} />}
          {tab === 'models' && <Models models={s.models} />}
          {tab === 'services' && <Services services={s.services} />}
          {tab === 'scans' && <Scans repo={repo} />}
          {tab === 'raw' && (
            <div className="card flush">
              <div className="card-head">
                <span className="muted small">
                  CycloneDX {bom.specVersion} · {bom.serialNumber}
                </span>
                <Button variant="ghost" size="sm" icon="download" onClick={() => downloadJson(bom, `${repo.name}.cdx.json`)}>
                  Download
                </Button>
              </div>
              <pre className="json">{JSON.stringify(bom, null, 2)}</pre>
            </div>
          )}
        </>
      )}
    </>
  )
}
