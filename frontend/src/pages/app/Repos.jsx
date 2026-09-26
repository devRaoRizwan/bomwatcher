import { useMemo, useState } from 'react'
import { Link, useOutletContext } from 'react-router-dom'
import { enableRepos, listRepos } from '../../api/bomwatcher'
import Icon from '../../components/Icon'
import { Alert, Button, EmptyState, Language, PageLoader, StatusBadge } from '../../components/ui'
import { useAsync } from '../../lib/hooks'
import { timeAgo } from '../../lib/format'

const IN_PROGRESS = new Set(['pr_open', 'scanning', 'pending'])
const FILTERS = [
  ['all', 'All'],
  ['enabled', 'Enabled'],
  ['not_enabled', 'Not enabled'],
]

export default function Repos() {
  const { installation, usage, refresh } = useOutletContext()
  const [selected, setSelected] = useState(new Set())
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState('all')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [notice, setNotice] = useState(null)

  const { data: repos, loading, error: loadError, reload } = useAsync(
    () => (installation ? listRepos() : Promise.resolve([])),
    installation?.id ?? null,
    { pollWhile: (rs) => rs?.some((r) => IN_PROGRESS.has(r.status)) },
  )

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase()
    return (repos ?? []).filter((r) => {
      if (q && !r.name.toLowerCase().includes(q) && !r.description?.toLowerCase().includes(q)) return false
      if (filter === 'enabled') return r.status !== 'not_enabled'
      if (filter === 'not_enabled') return r.status === 'not_enabled'
      return true
    })
  }, [repos, query, filter])

  if (!installation) {
    return (
      <>
        <div className="page-head">
          <h1>Repositories</h1>
        </div>
        <div className="card">
          <EmptyState icon="github" title="Connect GitHub first" action={<Link to="/app/github" className="btn btn-primary">Connect GitHub</Link>}>
            BOMWatcher needs the GitHub App installed before it can list your repositories.
          </EmptyState>
        </div>
      </>
    )
  }

  const selectable = visible.filter((r) => r.status === 'not_enabled')
  const slotsLeft = usage ? usage.repo_limit - usage.repos_enabled : Infinity
  const allSelected = selectable.length > 0 && selectable.every((r) => selected.has(r.id))

  const toggle = (id) =>
    setSelected((s) => {
      const n = new Set(s)
      if (n.has(id)) n.delete(id)
      else n.add(id)
      return n
    })

  const toggleAll = () => setSelected(allSelected ? new Set() : new Set(selectable.map((r) => r.id)))

  const enable = async () => {
    setBusy(true)
    setError(null)
    try {
      const { opened, errors } = await enableRepos([...selected])
      setNotice(
        opened
          ? `Opened ${opened} pull request${opened === 1 ? '' : 's'}. Merge ${opened === 1 ? 'it' : 'them'} on GitHub to start scanning.`
          : 'Scanning enabled. The workflow was already in place.',
      )
      if (errors?.length) setError(errors.join(' · '))
      setSelected(new Set())
      await Promise.all([reload(true), refresh()])
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Repositories</h1>
          <p className="muted">
            Repos the GitHub App can see on <strong>{installation.account.login}</strong>. Select some to add the scan
            workflow.
          </p>
        </div>
      </div>

      {error && <Alert onClose={() => setError(null)}>{error}</Alert>}
      {notice && (
        <Alert kind="success" onClose={() => setNotice(null)}>
          {notice}
        </Alert>
      )}
      {loadError && <Alert>{loadError.message}</Alert>}

      <div className="toolbar">
        <div className="search">
          <Icon name="search" size={16} />
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search repositories" aria-label="Search repositories" />
        </div>
        <div className="segmented" role="tablist">
          {FILTERS.map(([k, label]) => (
            <button key={k} role="tab" aria-selected={filter === k} className={filter === k ? 'active' : ''} onClick={() => setFilter(k)}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {loading && !repos ? (
        <PageLoader />
      ) : visible.length === 0 ? (
        <div className="card">
          <EmptyState icon="search" title="No repositories match">
            Try a different search or filter.
          </EmptyState>
        </div>
      ) : (
        <div className="card flush">
          <div className="list-head">
            <label className="check">
              <input type="checkbox" checked={allSelected} onChange={toggleAll} disabled={selectable.length === 0} />
              <span>{selected.size ? `${selected.size} selected` : 'Select all'}</span>
            </label>
            <span className="muted small">{visible.length} repositories</span>
          </div>
          <ul className="repo-list">
            {visible.map((r) => {
              const enabled = r.status !== 'not_enabled'
              return (
                <li key={r.id} className={`repo-row ${selected.has(r.id) ? 'selected' : ''}`}>
                  <label className="check">
                    <input
                      type="checkbox"
                      checked={enabled || selected.has(r.id)}
                      disabled={enabled}
                      onChange={() => toggle(r.id)}
                      aria-label={`Select ${r.name}`}
                    />
                  </label>
                  <div className="repo-main">
                    <div className="repo-name">
                      {enabled ? <Link to={`/app/repos/${r.id}`}>{r.name}</Link> : <span>{r.name}</span>}
                      <span className="chip">
                        <Icon name={r.private ? 'lock' : 'globe'} size={11} /> {r.private ? 'Private' : 'Public'}
                      </span>
                    </div>
                    {r.description && <p className="repo-desc">{r.description}</p>}
                    <div className="repo-meta">
                      <Language name={r.language} />
                      <span>Updated {timeAgo(r.updated_at)}</span>
                      {r.counts && (
                        <span>
                          {r.counts.libraries} libraries · {r.counts.models} models
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="repo-side">
                    <StatusBadge status={r.status} />
                    {r.status === 'pr_open' && r.pr && (
                      <a href={r.pr.url} target="_blank" rel="noreferrer" className="link-small">
                        PR #{r.pr.number} <Icon name="external" size={12} />
                      </a>
                    )}
                    {enabled && (
                      <Link to={`/app/repos/${r.id}`} className="link-small">
                        Details <Icon name="arrowRight" size={12} />
                      </Link>
                    )}
                  </div>
                </li>
              )
            })}
          </ul>
        </div>
      )}

      {selected.size > 0 && (
        <div className="action-bar">
          <span>
            <strong>{selected.size}</strong> repo{selected.size === 1 ? '' : 's'} selected
            {selected.size > slotsLeft && (
              <span className="warn-text">
                {' '}
                · only {slotsLeft} trial slot{slotsLeft === 1 ? '' : 's'} left
              </span>
            )}
          </span>
          <div className="row-actions">
            <Button variant="ghost" onClick={() => setSelected(new Set())}>
              Clear
            </Button>
            <Button icon="pr" onClick={enable} loading={busy} disabled={selected.size > slotsLeft}>
              Open workflow PR{selected.size === 1 ? '' : 's'}
            </Button>
          </div>
        </div>
      )}
    </>
  )
}
