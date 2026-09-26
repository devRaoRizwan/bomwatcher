import Icon from './Icon'

export function Spinner({ size = 16 }) {
  return <span className="spinner" style={{ width: size, height: size }} role="status" aria-label="Loading" />
}

export function PageLoader() {
  return (
    <div className="page-loader">
      <Spinner size={24} />
    </div>
  )
}

export function Button({ variant = 'primary', size, loading, icon, children, className = '', ...rest }) {
  return (
    <button className={`btn btn-${variant} ${size ? `btn-${size}` : ''} ${className}`} disabled={loading || rest.disabled} {...rest}>
      {loading ? <Spinner size={14} /> : icon && <Icon name={icon} size={16} />}
      {children}
    </button>
  )
}

export function Alert({ kind = 'error', children, onClose }) {
  return (
    <div className={`alert alert-${kind}`} role={kind === 'error' ? 'alert' : 'status'}>
      <Icon name={kind === 'error' ? 'alert' : kind === 'success' ? 'check' : 'zap'} size={16} />
      <div className="alert-body">{children}</div>
      {onClose && (
        <button className="icon-btn" onClick={onClose} aria-label="Dismiss">
          <Icon name="x" size={14} />
        </button>
      )}
    </div>
  )
}

export function EmptyState({ icon = 'package', title, children, action }) {
  return (
    <div className="empty">
      <div className="empty-icon">
        <Icon name={icon} size={22} />
      </div>
      <h3>{title}</h3>
      {children && <p>{children}</p>}
      {action}
    </div>
  )
}

export function Avatar({ name = '?', size = 32 }) {
  const initials = name.replace(/@.*/, '').split(/[.\-_ ]+/).filter(Boolean).slice(0, 2).map((s) => s[0]).join('').toUpperCase() || '?'
  let hue = 0
  for (const ch of name) hue = (hue * 31 + ch.charCodeAt(0)) % 360
  return (
    <span className="avatar" style={{ width: size, height: size, fontSize: size * 0.38, '--hue': hue }} aria-hidden="true">
      {initials}
    </span>
  )
}

const STATUS = {
  not_enabled: { label: 'Not enabled', tone: 'muted' },
  pr_open: { label: 'Awaiting PR merge', tone: 'warn', icon: 'pr' },
  pending: { label: 'Waiting for first run', tone: 'info' },
  scanning: { label: 'Scanning', tone: 'info', spin: true },
  scanned: { label: 'Scanned', tone: 'ok', icon: 'check' },
  running: { label: 'Running', tone: 'info', spin: true },
  success: { label: 'Success', tone: 'ok', icon: 'check' },
  failure: { label: 'Failed', tone: 'bad', icon: 'x' },
  failed: { label: 'Last scan failed', tone: 'bad', icon: 'x' },
}

export function StatusBadge({ status }) {
  const s = STATUS[status] ?? { label: status, tone: 'muted' }
  return (
    <span className={`badge badge-${s.tone}`}>
      {s.spin ? <span className="pulse-dot" /> : s.icon && <Icon name={s.icon} size={12} strokeWidth={2.4} />}
      {s.label}
    </span>
  )
}

const LANG_COLORS = { Python: '#3572A5', TypeScript: '#3178c6', JavaScript: '#f1e05a', Shell: '#89e051', Go: '#00ADD8' }
export function Language({ name }) {
  if (!name) return null
  return (
    <span className="lang">
      <span className="lang-dot" style={{ background: LANG_COLORS[name] ?? '#8b949e' }} />
      {name}
    </span>
  )
}
