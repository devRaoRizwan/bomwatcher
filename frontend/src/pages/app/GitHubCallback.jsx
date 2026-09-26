import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useOutletContext, useSearchParams } from 'react-router-dom'
import { completeInstallation } from '../../api/bomwatcher'
import { EmptyState, PageLoader } from '../../components/ui'

export default function GitHubCallback() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const { refresh } = useOutletContext()
  const [error, setError] = useState(null)
  const started = useRef(false)

  useEffect(() => {
    if (started.current) return
    started.current = true
    const installationId = params.get('installation_id')
    const state = params.get('state')
    if (!installationId || !state) {
      setError('GitHub did not return an installation. Try connecting again.')
      return
    }
    completeInstallation(installationId, state)
      .then(refresh)
      .then(() => navigate('/app/repos', { replace: true }))
      .catch((e) => setError(e.message))
  }, [params, navigate, refresh])

  if (!error) return <PageLoader />
  return (
    <div className="card">
      <EmptyState icon="alert" title="Couldn't finish connecting GitHub" action={<Link to="/app/github" className="btn btn-primary">Try again</Link>}>
        {error}
      </EmptyState>
    </div>
  )
}
