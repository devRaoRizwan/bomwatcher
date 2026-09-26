import { Link, useOutletContext } from 'react-router-dom'
import { USE_MOCKS } from '../../api/bomwatcher'
import Icon from '../../components/Icon'
import { Avatar, Button } from '../../components/ui'
import { useAuth } from '../../context/useAuth'

export default function Settings() {
  const { email, logout } = useAuth()
  const { installation, usage } = useOutletContext()

  const resetDemo = () => {
    if (!confirm('Clear all simulated GitHub and scan data for this account?')) return
    localStorage.removeItem(`bomwatcher.mock.${email}`)
    window.location.assign('/app')
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Settings</h1>
          <p className="muted">Account, plan and connection details.</p>
        </div>
      </div>

      <div className="card settings-section">
        <h3 className="card-title">Account</h3>
        <div className="settings-row">
          <Avatar name={email ?? '?'} size={40} />
          <div className="grow">
            <div className="strong">{email}</div>
            <div className="muted small">Signed in with email and password</div>
          </div>
          <Button
            variant="secondary"
            icon="logout"
            onClick={() => logout()}
          >
            Log out
          </Button>
        </div>
      </div>

      <div className="card settings-section">
        <h3 className="card-title">Plan</h3>
        <div className="settings-row">
          <div className="grow">
            <div className="strong">Free trial</div>
            <div className="muted small">
              {usage ? `${usage.repos_enabled} of ${usage.repo_limit} repos in use` : 'Loading usage…'}
            </div>
          </div>
          <span className="chip">Team plan coming soon</span>
        </div>
      </div>

      <div className="card settings-section">
        <h3 className="card-title">GitHub</h3>
        <div className="settings-row">
          <Icon name="github" size={22} />
          <div className="grow">
            <div className="strong">{installation ? installation.account.login : 'Not connected'}</div>
            <div className="muted small">{installation ? 'BOMWatcher GitHub App installed' : 'Install the GitHub App to start scanning'}</div>
          </div>
          <Link to="/app/github" className="btn btn-secondary">
            Manage
          </Link>
        </div>
      </div>

      {USE_MOCKS && (
        <div className="card settings-section">
          <h3 className="card-title">Demo data</h3>
          <div className="settings-row">
            <div className="grow muted small">Simulated repos, PRs and scans are stored in this browser. Reset them to go through onboarding again.</div>
            <Button variant="danger-ghost" onClick={resetDemo}>
              Reset demo data
            </Button>
          </div>
        </div>
      )}
    </>
  )
}
