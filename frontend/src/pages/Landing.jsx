import { Link } from 'react-router-dom'
import Icon from '../components/Icon'
import Logo from '../components/Logo'
import { useAuth } from '../context/useAuth'
import { TRIAL_REPO_LIMIT } from '../api/mock'

const STEPS = [
  { icon: 'github', title: 'Connect GitHub', body: 'Install the BOMWatcher GitHub App on your account or org. You choose which repos it can see.' },
  { icon: 'repo', title: 'Pick repos', body: 'Select some or all of your repositories to inventory.' },
  { icon: 'pr', title: 'Merge one PR', body: 'BOMWatcher opens a PR adding a small bomwatcher-scan.yml workflow. You review it and merge it.' },
  { icon: 'play', title: 'Scan runs on your runners', body: 'The workflow runs on GitHub Actions using your minutes. Your source code never leaves GitHub.' },
  { icon: 'file', title: 'CycloneDX AI-BOM', body: 'The workflow produces a CycloneDX 1.6 BOM and uploads it as a build artifact.' },
  { icon: 'dashboard', title: 'See the results', body: 'BOMWatcher pulls the artifact, parses it, and shows every dependency, model and AI service.' },
]

const FEATURES = [
  { icon: 'package', title: 'Dependency inventory', body: 'Every library by ecosystem, version, scope and license, with package URLs you can trace.' },
  { icon: 'cpu', title: 'AI model usage', body: 'Hosted models called through SDKs and open-weight models loaded locally, listed as machine-learning-model components.' },
  { icon: 'cloud', title: 'AI services', body: 'The external AI APIs your code calls, and the endpoints it calls them on.' },
  { icon: 'shield', title: 'License review flags', body: 'Copyleft and non-commercial licenses are flagged so you catch them before release, not after.' },
]

const SAMPLE = `{
  "bomFormat": "CycloneDX",
  "specVersion": "1.6",
  "components": [
    {
      "type": "library",
      "name": "anthropic",
      "version": "0.42.0",
      "purl": "pkg:pypi/anthropic@0.42.0"
    },
    {
      "type": "machine-learning-model",
      "name": "claude-sonnet-5",
      "supplier": { "name": "Anthropic" },
      "modelCard": {
        "modelParameters": { "task": "text-generation" }
      }
    }
  ]
}`

export default function Landing() {
  const { isAuthenticated } = useAuth()
  return (
    <div className="landing">
      <header className="landing-nav">
        <div className="container nav-inner">
          <Logo />
          <nav className="nav-links">
            <a href="#how">How it works</a>
            <a href="#features">What you get</a>
            <a href="#pricing">Pricing</a>
          </nav>
          <div className="nav-cta">
            {isAuthenticated ? (
              <Link to="/app" className="btn btn-primary">
                Open dashboard
              </Link>
            ) : (
              <>
                <Link to="/login" className="btn btn-ghost">
                  Log in
                </Link>
                <Link to="/signup" className="btn btn-primary">
                  Start free
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      <section className="hero">
        <div className="container hero-grid">
          <div>
            <span className="eyebrow">
              <Icon name="shield" size={14} /> CycloneDX AI-BOM for GitHub repos
            </span>
            <h1>Know every dependency and AI model your code ships with</h1>
            <p className="lead">
              Connect GitHub, pick your repos, and get a Bill of Materials covering libraries and AI models. The scan
              runs on <strong>your own GitHub Actions minutes</strong>, so your code never touches our servers.
            </p>
            <div className="hero-cta">
              <Link to={isAuthenticated ? '/app' : '/signup'} className="btn btn-primary btn-lg">
                {isAuthenticated ? 'Go to dashboard' : 'Scan your repos free'} <Icon name="arrowRight" size={16} />
              </Link>
              <a href="#how" className="btn btn-secondary btn-lg">
                See how it works
              </a>
            </div>
            <p className="hero-note">Free trial covers {TRIAL_REPO_LIMIT} repos. No credit card.</p>
          </div>
          <div className="code-window" aria-label="Example CycloneDX output">
            <div className="code-window-bar">
              <span />
              <span />
              <span />
              <em>bom.cdx.json</em>
            </div>
            <pre>{SAMPLE}</pre>
          </div>
        </div>
      </section>

      <section id="how" className="section">
        <div className="container">
          <h2 className="section-title">How it works</h2>
          <p className="section-sub">The scan is a stage in your pipeline, running where your code already lives.</p>
          <ol className="steps">
            {STEPS.map((s, i) => (
              <li key={s.title} className="step">
                <div className="step-num">{i + 1}</div>
                <div>
                  <h3>
                    <Icon name={s.icon} size={16} /> {s.title}
                  </h3>
                  <p>{s.body}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section id="features" className="section section-alt">
        <div className="container">
          <h2 className="section-title">What's in the BOM</h2>
          <p className="section-sub">Standard CycloneDX JSON. Download it and feed it to any tool that reads the format.</p>
          <div className="feature-grid">
            {FEATURES.map((f) => (
              <div key={f.title} className="card feature">
                <div className="feature-icon">
                  <Icon name={f.icon} size={20} />
                </div>
                <h3>{f.title}</h3>
                <p>{f.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container why">
          <div>
            <h2 className="section-title left">Why run it on your runners?</h2>
            <p>
              Most scanners want a copy of your code. BOMWatcher sends a workflow to your repo instead. GitHub runs it,
              and the only thing BOMWatcher receives is the finished BOM artifact.
            </p>
          </div>
          <ul className="checklist">
            <li>
              <Icon name="check" size={16} /> Source code stays on GitHub's infrastructure
            </li>
            <li>
              <Icon name="check" size={16} /> You review the workflow before it runs, since it arrives as a PR
            </li>
            <li>
              <Icon name="check" size={16} /> Uses Actions minutes you already have
            </li>
            <li>
              <Icon name="check" size={16} /> Re-scans on every push to your default branch
            </li>
          </ul>
        </div>
      </section>

      <section id="pricing" className="section section-alt">
        <div className="container">
          <h2 className="section-title">Pricing</h2>
          <div className="pricing">
            <div className="card price-card featured">
              <h3>Free trial</h3>
              <div className="price">
                $0
              </div>
              <ul className="checklist">
                <li>
                  <Icon name="check" size={16} /> Up to {TRIAL_REPO_LIMIT} repositories
                </li>
                <li>
                  <Icon name="check" size={16} /> Unlimited scans
                </li>
                <li>
                  <Icon name="check" size={16} /> CycloneDX 1.6 JSON download
                </li>
              </ul>
              <Link to="/signup" className="btn btn-primary btn-block">
                Start free
              </Link>
            </div>
            <div className="card price-card">
              <h3>Team</h3>
              <div className="price muted-price">Coming soon</div>
              <ul className="checklist">
                <li>
                  <Icon name="check" size={16} /> Unlimited repositories
                </li>
                <li>
                  <Icon name="check" size={16} /> Org-wide rollout
                </li>
                <li>
                  <Icon name="check" size={16} /> BOM history and diffs
                </li>
              </ul>
              <button className="btn btn-secondary btn-block" disabled>
                Join waitlist
              </button>
            </div>
          </div>
        </div>
      </section>

      <footer className="footer">
        <div className="container footer-inner">
          <Logo />
          <p>
            Built by{' '}
            <a href="https://github.com/devRaoRizwan" target="_blank" rel="noreferrer">
              Rao Rizwan
            </a>
          </p>
        </div>
      </footer>
    </div>
  )
}
