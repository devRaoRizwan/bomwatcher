import { Link } from 'react-router-dom'

export default function Logo({ to = '/' }) {
  return (
    <Link to={to} className="logo">
      <img src="/favicon.svg" alt="" width="28" height="28" className="logo-mark" />
      BOMWatcher
    </Link>
  )
}
