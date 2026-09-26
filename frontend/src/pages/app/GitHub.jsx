import { useState } from 'react'
import { Link, useNavigate, useOutletContext } from 'react-router-dom'
import { connectGitHub, disconnectGitHub } from '../../api/bomwatcher'
import Icon from '../../components/Icon'
import { Alert, Avatar, Button } from '../../components/ui'
import { formatDate } from '../../lib/format'

const PERMISSIONS = [
  ['Contents', 'Read & write', 'to commit the workflow file on a new branch'],
  ['Pull requests', 'Read & write', 'to open the PR that adds the workflow'],
  ['Workflows', 'Read & write', 'required by GitHub to add files under .github/workflows'],
  ['Actions', 'Read & write', 'to download the BOM artifact and trigger re-scans'],
  ['Metadata', 'Read', 'to list your repositories'],
]

export default function GitHub() {
  const { installation, refresh } = useOutletContext()
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const connect = async () => {
    setBusy(true)
    setError(null)
    try {
      await connectGitHub()
      await refresh()
      navigate('/app/repos')
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const disconnect = async () => {
    if (!confirm('Disconnect GitHub? BOMWatcher will stop tracking all repos. Workflow files already merged stay in your repos until you remove them.')) return
    setBusy(true)
    try {
      await disconnectGitHub()
      await refresh()
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
          <h1>GitHub connection</h1>
          <p className="muted">BOMWatcher works through a GitHub App installed on your account.</p>
        </div>
      </div>

      {error && <Alert onClose={() => setError(null)}>{error}</Alert>}

      {installation ? (
        <div className="card">
          <div className="gh-connected">
            <Avatar name={installation.account.login} size={48} />
            <div className="grow">
              <div className="gh-login">
                <Icon name="github" size={16} /> {installation.account.login}
                <span className="badge badge-ok">
                  <Icon name="check" size={12} strokeWidth={2.4} /> Connected
                </span>
              </div>
              <p className="muted small">
                {installation.account.type} account · installed {formatDate(installation.installed_at)} · access to{' '}
                {installation.repository_selection === 'all' ? 'all repositories' : 'selected repositories'}
              </p>
            </div>
            <div className="row-actions">
              <Link to="/app/repos" className="btn btn-primary">
                Choose repos
              </Link>
              <Button variant="danger-ghost" onClick={disconnect} loading={busy}>
                Disconnect
              </Button>
            </div>
          </div>
        </div>
      ) : (
        <div className="card connect-card">
          <div className="connect-hero">
            <div className="connect-icon">
              <Icon name="github" size={28} />
            </div>
            <h2>Connect your GitHub account</h2>
            <p className="muted">
              You'll be sent to GitHub to install the BOMWatcher app. Pick all repos or only the ones you want, and you can
              change that later from GitHub's settings.
            </p>
            <Button size="lg" icon="github" onClick={connect} loading={busy}>
              Install GitHub App
            </Button>
          </div>
        </div>
      )}

      <div className="card">
        <h3 className="card-title">Permissions the app requests</h3>
        <table className="table">
          <thead>
            <tr>
              <th>Permission</th>
              <th>Access</th>
              <th>Why</th>
            </tr>
          </thead>
          <tbody>
            {PERMISSIONS.map(([p, a, why]) => (
              <tr key={p}>
                <td className="strong">{p}</td>
                <td>
                  <span className="chip">{a}</span>
                </td>
                <td className="muted">{why}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="muted small note">
          <Icon name="lock" size={14} /> BOMWatcher never clones your code. It only writes one workflow file (through a PR you
          merge) and reads the BOM artifact that workflow uploads.
        </p>
      </div>
    </>
  )
}
