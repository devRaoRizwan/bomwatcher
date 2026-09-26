export const isModel = (c) => c.type === 'machine-learning-model'
export const isLibrary = (c) => c.type === 'library'

export function ecosystemOf(c) {
  const m = c.purl?.match(/^pkg:([^/]+)\//)
  return m ? m[1] : null
}

export function licenseOf(c) {
  const l = c.licenses?.[0]
  return l?.license?.id ?? l?.license?.name ?? l?.expression ?? null
}

export function property(c, name) {
  return c.properties?.find((p) => p.name === name)?.value ?? null
}

const REVIEW_LICENSES = /^(A?GPL|LGPL|MPL|EPL|CC-BY-NC|SSPL|BUSL)/i
export const needsLicenseReview = (id) => !!id && REVIEW_LICENSES.test(id)

function tally(items, keyFn) {
  const out = {}
  for (const it of items) {
    const k = keyFn(it) ?? 'Unknown'
    out[k] = (out[k] ?? 0) + 1
  }
  return Object.entries(out).sort((a, b) => b[1] - a[1])
}

export function summarize(bom) {
  const components = bom?.components ?? []
  const libraries = components.filter(isLibrary)
  const models = components.filter(isModel)
  return {
    libraries,
    models,
    services: bom?.services ?? [],
    direct: libraries.filter((c) => c.scope !== 'optional').length,
    ecosystems: tally(libraries, ecosystemOf),
    licenses: tally(components.filter((c) => c.licenses), licenseOf),
    providers: tally(models, (m) => m.supplier?.name),
    reviewCount: components.filter((c) => needsLicenseReview(licenseOf(c))).length,
  }
}

export function downloadJson(data, filename) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = Object.assign(document.createElement('a'), { href: url, download: filename })
  a.click()
  URL.revokeObjectURL(url)
}
