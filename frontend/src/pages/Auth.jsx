import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import Logo from '../components/Logo'
import { Alert, Button } from '../components/ui'
import { useAuth } from '../context/useAuth'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function AuthForm({ mode }) {
  const isSignup = mode === 'signup'
  const { login, signup, sessionExpired } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ email: '', password: '', confirm: '' })
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const validate = () => {
    if (!EMAIL_RE.test(form.email)) return 'Enter a valid email address.'
    if (form.email.length > 50) return 'Email must be 50 characters or fewer.'
    if (isSignup && form.password.length < 8) return 'Password must be at least 8 characters.'
    if (!form.password) return 'Enter your password.'
    if (isSignup && form.password !== form.confirm) return "Passwords don't match."
    return null
  }

  const onSubmit = async (e) => {
    e.preventDefault()
    const problem = validate()
    if (problem) return setError(problem)
    setError(null)
    setLoading(true)
    try {
      const email = form.email.trim().toLowerCase()
      if (isSignup) await signup(email, form.password)
      else await login(email, form.password)
      navigate(isSignup ? '/app/github' : (location.state?.from ?? '/app'), { replace: true })
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card card">
        <Logo />
        <h1>{isSignup ? 'Create your account' : 'Welcome back'}</h1>
        <p className="muted">{isSignup ? 'Start scanning your repos in a couple of minutes.' : 'Log in to see your repos and BOMs.'}</p>

        {sessionExpired && !isSignup && !error && <Alert kind="info">Your session expired. Log in again to continue.</Alert>}
        {error && <Alert onClose={() => setError(null)}>{error}</Alert>}

        <form onSubmit={onSubmit} noValidate className="form">
          <label className="field">
            <span>Email</span>
            <input type="email" autoComplete="email" value={form.email} onChange={set('email')} placeholder="you@company.com" autoFocus />
          </label>
          <label className="field">
            <span>Password</span>
            <input
              type="password"
              autoComplete={isSignup ? 'new-password' : 'current-password'}
              value={form.password}
              onChange={set('password')}
              placeholder={isSignup ? 'At least 8 characters' : ''}
            />
          </label>
          {isSignup && (
            <label className="field">
              <span>Confirm password</span>
              <input type="password" autoComplete="new-password" value={form.confirm} onChange={set('confirm')} />
            </label>
          )}
          <Button type="submit" loading={loading} className="btn-block">
            {isSignup ? 'Create account' : 'Log in'}
          </Button>
        </form>

        <p className="auth-switch">
          {isSignup ? (
            <>
              Already have an account? <Link to="/login">Log in</Link>
            </>
          ) : (
            <>
              New to BOMWatcher? <Link to="/signup">Create an account</Link>
            </>
          )}
        </p>
      </div>
    </div>
  )
}

export const Login = () => <AuthForm mode="login" />
export const Signup = () => <AuthForm mode="signup" />
