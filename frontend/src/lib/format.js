const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })
const UNITS = [
  ['year', 31_536_000], ['month', 2_592_000], ['week', 604_800],
  ['day', 86_400], ['hour', 3_600], ['minute', 60], ['second', 1],
]

export function timeAgo(iso) {
  if (!iso) return '—'
  const secs = (new Date(iso).getTime() - Date.now()) / 1000
  for (const [unit, size] of UNITS) {
    if (Math.abs(secs) >= size || unit === 'second') {
      if (unit === 'second' && Math.abs(secs) < 10) return 'just now'
      return rtf.format(Math.round(secs / size), unit)
    }
  }
}

export function formatDate(iso) {
  return iso ? new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }) : '—'
}

export function duration(startIso, endIso) {
  if (!startIso || !endIso) return '—'
  const s = Math.round((new Date(endIso) - new Date(startIso)) / 1000)
  return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60}s`
}
