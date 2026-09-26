import { Link } from 'react-router-dom'
import Icon from './Icon'

export default function Logo({ to = '/' }) {
  return (
    <Link to={to} className="logo">
      <span className="logo-mark">
        <Icon name="logo" size={16} strokeWidth={2.4} />
      </span>
      BOMWatcher
    </Link>
  )
}
