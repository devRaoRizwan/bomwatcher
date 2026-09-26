import { ApiError } from './client'

export const TRIAL_REPO_LIMIT = 3
const PR_OPEN_MS = 10_000
const SCAN_RUN_MS = 8_000

const delay = (ms = 350) => new Promise((r) => setTimeout(r, ms + Math.random() * 250))

function stateKey() {
  return `bomwatcher.mock.${localStorage.getItem('bomwatcher.email') ?? 'anon'}`
}

function load() {
  try {
    return JSON.parse(localStorage.getItem(stateKey())) ?? { installation: null, repos: {} }
  } catch {
    return { installation: null, repos: {} }
  }
}

function save(state) {
  localStorage.setItem(stateKey(), JSON.stringify(state))
}

const now = () => Date.now()
const daysAgo = (d) => new Date(now() - d * 86_400_000).toISOString()

const REPO_CATALOG = [
  { id: 101, name: 'support-copilot', language: 'Python', description: 'RAG chatbot answering support tickets from the internal knowledge base.', private: true, updated: 1, stars: 4 },
  { id: 102, name: 'invoice-extractor', language: 'Python', description: 'Pulls line items from PDF invoices using an LLM + OCR pipeline.', private: true, updated: 3, stars: 0 },
  { id: 103, name: 'storefront-web', language: 'TypeScript', description: 'Next.js storefront with AI product-description generator.', private: false, updated: 2, stars: 31 },
  { id: 104, name: 'payments-api', language: 'Python', description: 'Django REST API handling checkout and refunds.', private: true, updated: 6, stars: 2 },
  { id: 105, name: 'recsys-embeddings', language: 'Python', description: 'Nightly job building product embeddings for recommendations.', private: true, updated: 9, stars: 1 },
  { id: 106, name: 'ops-scripts', language: 'Shell', description: 'Deploy and maintenance scripts.', private: true, updated: 21, stars: 0 },
  { id: 107, name: 'mobile-app', language: 'TypeScript', description: 'React Native client for the storefront.', private: false, updated: 12, stars: 12 },
  { id: 108, name: 'dotfiles', language: 'Shell', description: null, private: false, updated: 40, stars: 3 },
]

const PY_LIBS = [
  ['fastapi', '0.115.6', 'MIT'], ['pydantic', '2.10.4', 'MIT'], ['sqlalchemy', '2.0.36', 'MIT'],
  ['httpx', '0.28.1', 'BSD-3-Clause'], ['uvicorn', '0.34.0', 'BSD-3-Clause'], ['celery', '5.4.0', 'BSD-3-Clause'],
  ['redis', '5.2.1', 'MIT'], ['numpy', '2.2.1', 'BSD-3-Clause'], ['pandas', '2.2.3', 'BSD-3-Clause'],
  ['requests', '2.32.3', 'Apache-2.0'], ['python-dotenv', '1.0.1', 'BSD-3-Clause'], ['pyjwt', '2.10.1', 'MIT'],
  ['psycopg', '3.2.3', 'LGPL-3.0-only'], ['boto3', '1.35.90', 'Apache-2.0'], ['tenacity', '9.0.0', 'Apache-2.0'],
]
const PY_AI_LIBS = [
  ['anthropic', '0.42.0', 'MIT'], ['openai', '1.59.3', 'Apache-2.0'], ['langchain', '0.3.14', 'MIT'],
  ['tiktoken', '0.8.0', 'MIT'], ['sentence-transformers', '3.3.1', 'Apache-2.0'], ['transformers', '4.47.1', 'Apache-2.0'],
  ['torch', '2.5.1', 'BSD-3-Clause'], ['faiss-cpu', '1.9.0', 'MIT'], ['pypdf', '5.1.0', 'BSD-3-Clause'],
]
const JS_LIBS = [
  ['next', '15.1.3', 'MIT'], ['react', '19.0.0', 'MIT'], ['react-dom', '19.0.0', 'MIT'], ['zod', '3.24.1', 'MIT'],
  ['axios', '1.7.9', 'MIT'], ['date-fns', '4.1.0', 'MIT'], ['tailwindcss', '3.4.17', 'MIT'],
  ['@tanstack/react-query', '5.62.11', 'MIT'], ['sharp', '0.33.5', 'Apache-2.0'], ['stripe', '17.5.0', 'MIT'],
  ['react-native', '0.76.5', 'MIT'], ['expo', '52.0.23', 'MIT'],
]
const JS_AI_LIBS = [['ai', '4.0.22', 'Apache-2.0'], ['@anthropic-ai/sdk', '0.33.1', 'MIT'], ['openai', '4.77.0', 'Apache-2.0']]

const MODELS = {
  'claude-sonnet-5': { provider: 'Anthropic', task: 'text-generation', hosting: 'API', source: 'anthropic SDK call' },
  'claude-haiku-4-5': { provider: 'Anthropic', task: 'text-generation', hosting: 'API', source: 'anthropic SDK call' },
  'gpt-4o-mini': { provider: 'OpenAI', task: 'text-generation', hosting: 'API', source: 'openai SDK call' },
  'text-embedding-3-small': { provider: 'OpenAI', task: 'feature-extraction', hosting: 'API', source: 'openai SDK call' },
  'sentence-transformers/all-MiniLM-L6-v2': { provider: 'Hugging Face', task: 'feature-extraction', hosting: 'Self-hosted', source: 'transformers load', license: 'Apache-2.0' },
  'microsoft/layoutlmv3-base': { provider: 'Hugging Face', task: 'document-question-answering', hosting: 'Self-hosted', source: 'transformers load', license: 'CC-BY-NC-SA-4.0' },
}

const REPO_PROFILE = {
  101: { libs: [0, 1, 2, 3, 4, 10, 13], ai: [0, 2, 3, 7], models: ['claude-sonnet-5', 'claude-haiku-4-5', 'text-embedding-3-small'] },
  102: { libs: [0, 1, 3, 6, 5, 9, 12, 14], ai: [1, 8, 5, 6], models: ['gpt-4o-mini', 'microsoft/layoutlmv3-base'] },
  103: { js: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], jsai: [0, 1], models: ['claude-haiku-4-5'] },
  104: { libs: [1, 2, 3, 5, 6, 9, 10, 11, 12, 14], ai: [], models: [] },
  105: { libs: [7, 8, 9, 13, 10], ai: [4, 6, 7], models: ['sentence-transformers/all-MiniLM-L6-v2'] },
  106: { libs: [], ai: [], models: [] },
  107: { js: [1, 3, 4, 5, 7, 10, 11], jsai: [2], models: ['gpt-4o-mini'] },
  108: { libs: [], ai: [], models: [] },
}

function library(ecosystem, [name, version, license], scope = 'required') {
  const purl = `pkg:${ecosystem}/${name.replace('@', '%40')}@${version}`
  return { type: 'library', 'bom-ref': purl, name, version, purl, scope, licenses: [{ license: { id: license } }] }
}

function model(name) {
  const m = MODELS[name]
  const hf = m.provider === 'Hugging Face'
  return {
    type: 'machine-learning-model',
    'bom-ref': hf ? `pkg:huggingface/${name}` : `model:${m.provider.toLowerCase()}/${name}`,
    name,
    ...(hf ? { purl: `pkg:huggingface/${name}` } : {}),
    supplier: { name: m.provider },
    ...(m.license ? { licenses: [{ license: { id: m.license } }] } : {}),
    modelCard: { modelParameters: { task: m.task } },
    properties: [
      { name: 'bomwatcher:hosting', value: m.hosting },
      { name: 'bomwatcher:detectedVia', value: m.source },
    ],
  }
}

function buildBom(repo, owner, scannedAt, commit) {
  const p = REPO_PROFILE[repo.id] ?? { libs: [], ai: [], models: [] }
  const components = [
    ...(p.libs ?? []).map((i) => library('pypi', PY_LIBS[i])),
    ...(p.ai ?? []).map((i) => library('pypi', PY_AI_LIBS[i])),
    ...(p.js ?? []).map((i) => library('npm', JS_LIBS[i])),
    ...(p.jsai ?? []).map((i) => library('npm', JS_AI_LIBS[i])),
    ...p.models.map(model),
  ]
  if (p.libs?.includes(0)) components.push(library('pypi', ['starlette', '0.41.3', 'BSD-3-Clause'], 'optional'), library('pypi', ['anyio', '4.7.0', 'MIT'], 'optional'))
  if (p.js?.length) components.push(library('npm', ['scheduler', '0.25.0', 'MIT'], 'optional'), library('npm', ['tslib', '2.8.1', '0BSD'], 'optional'))

  const services = []
  if (p.models.some((m) => MODELS[m].provider === 'Anthropic')) services.push({ 'bom-ref': 'svc:anthropic', name: 'Anthropic API', endpoints: ['https://api.anthropic.com/v1/messages'], provider: { name: 'Anthropic' } })
  if (p.models.some((m) => MODELS[m].provider === 'OpenAI')) services.push({ 'bom-ref': 'svc:openai', name: 'OpenAI API', endpoints: ['https://api.openai.com/v1'], provider: { name: 'OpenAI' } })

  return {
    bomFormat: 'CycloneDX',
    specVersion: '1.6',
    serialNumber: `urn:uuid:${crypto.randomUUID()}`,
    version: 1,
    metadata: {
      timestamp: new Date(scannedAt).toISOString(),
      tools: { components: [{ type: 'application', name: 'bomwatcher-scan', version: '0.1.0' }] },
      component: { type: 'application', name: repo.name, 'bom-ref': `repo:${owner}/${repo.name}`, properties: [{ name: 'git:commit', value: commit }] },
    },
    components,
    services,
  }
}

function sha() {
  return Array.from(crypto.getRandomValues(new Uint8Array(20)), (b) => b.toString(16).padStart(2, '0')).join('')
}

function tick(state) {
  const owner = state.installation?.account.login
  let changed = false
  for (const r of Object.values(state.repos)) {
    if (!r.enabledAt) continue
    const mergedAt = r.enabledAt + PR_OPEN_MS
    if (!r.prMergedAt && now() >= mergedAt) {
      r.prMergedAt = mergedAt
      r.scans.unshift({ id: sha().slice(0, 10), status: 'running', trigger: 'push', startedAt: mergedAt, commit: sha() })
      changed = true
    }
    for (const s of r.scans) {
      if (s.status === 'running' && now() >= s.startedAt + SCAN_RUN_MS) {
        s.status = 'success'
        s.finishedAt = s.startedAt + SCAN_RUN_MS
        s.bom = buildBom(REPO_CATALOG.find((c) => c.id === r.id), owner, s.finishedAt, s.commit)
        changed = true
      }
    }
  }
  if (changed) save(state)
  return state
}

function repoStatus(r) {
  if (!r?.enabledAt) return 'not_enabled'
  if (!r.prMergedAt) return 'pr_open'
  if (r.scans[0]?.status === 'running') return 'scanning'
  if (r.scans.some((s) => s.status === 'success')) return 'scanned'
  return 'pending'
}

function repoView(catalog, r, owner) {
  const latest = r?.scans.find((s) => s.status === 'success')
  return {
    id: catalog.id,
    name: catalog.name,
    full_name: `${owner}/${catalog.name}`,
    description: catalog.description,
    language: catalog.language,
    private: catalog.private,
    stars: catalog.stars,
    default_branch: 'main',
    updated_at: daysAgo(catalog.updated),
    status: repoStatus(r),
    pr: r?.enabledAt ? { number: r.prNumber, url: `https://github.com/${owner}/${catalog.name}/pull/${r.prNumber}`, merged: !!r.prMergedAt, opened_at: new Date(r.enabledAt).toISOString() } : null,
    last_scan_at: latest ? new Date(latest.finishedAt).toISOString() : null,
    counts: latest ? countComponents(latest.bom) : null,
  }
}

function countComponents(bom) {
  const libraries = bom.components.filter((c) => c.type === 'library').length
  const models = bom.components.filter((c) => c.type === 'machine-learning-model').length
  return { libraries, models, services: bom.services.length }
}

function requireInstallation(state) {
  if (!state.installation) throw new ApiError('GitHub account not connected', 409)
}

export async function getInstallation() {
  await delay(150)
  return load().installation
}

export async function connectGitHub() {
  await delay(1200)
  const state = load()
  const email = localStorage.getItem('bomwatcher.email') ?? 'dev@example.com'
  const login = email.split('@')[0].replace(/[^a-zA-Z0-9-]/g, '-').toLowerCase() || 'octocat'
  state.installation = {
    id: Math.floor(Math.random() * 9e7) + 1e7,
    account: { login, type: 'User', avatar_url: `https://github.com/identicons/${login}.png` },
    repository_selection: 'all',
    installed_at: new Date().toISOString(),
  }
  save(state)
  return state.installation
}

export async function completeInstallation() {
  return load().installation
}

export async function disconnectGitHub() {
  await delay()
  save({ installation: null, repos: {} })
}

export async function listRepos() {
  await delay()
  const state = tick(load())
  requireInstallation(state)
  const owner = state.installation.account.login
  return REPO_CATALOG.map((c) => repoView(c, state.repos[c.id], owner))
}

export async function getUsage() {
  await delay(100)
  const state = load()
  const used = Object.values(state.repos).filter((r) => r.enabledAt).length
  return { plan: 'trial', repo_limit: TRIAL_REPO_LIMIT, repos_enabled: used }
}

export async function enableRepos(ids) {
  await delay(900)
  const state = load()
  requireInstallation(state)
  const already = Object.values(state.repos).filter((r) => r.enabledAt).length
  const fresh = ids.filter((id) => !state.repos[id]?.enabledAt)
  if (already + fresh.length > TRIAL_REPO_LIMIT) {
    throw new ApiError(`Free trial allows ${TRIAL_REPO_LIMIT} repos. You have ${TRIAL_REPO_LIMIT - already} slot(s) left.`, 402)
  }
  fresh.forEach((id, i) => {
    state.repos[id] = { id, enabledAt: now() + i * 1500, prNumber: 10 + Math.floor(Math.random() * 80), prMergedAt: null, scans: [] }
  })
  save(state)
  return { opened: fresh.length, already_configured: 0, errors: [] }
}

export async function disableRepo(id) {
  await delay()
  const state = load()
  delete state.repos[id]
  save(state)
}

export async function getRepo(id) {
  await delay()
  const state = tick(load())
  requireInstallation(state)
  const catalog = REPO_CATALOG.find((c) => c.id === Number(id))
  if (!catalog) throw new ApiError('Repository not found', 404)
  const r = state.repos[catalog.id]
  return {
    ...repoView(catalog, r, state.installation.account.login),
    scans: (r?.scans ?? []).map((s) => ({
      id: s.id,
      status: s.status,
      trigger: s.trigger,
      commit_sha: s.commit,
      run_url: null,
      started_at: new Date(s.startedAt).toISOString(),
      finished_at: s.finishedAt ? new Date(s.finishedAt).toISOString() : null,
      counts: s.bom ? countComponents(s.bom) : null,
      error: null,
    })),
  }
}

export async function getBom(repoId, scanId) {
  await delay(250)
  const state = tick(load())
  const r = state.repos[Number(repoId)]
  const scan = scanId ? r?.scans.find((s) => s.id === scanId) : r?.scans.find((s) => s.status === 'success')
  if (!scan?.bom) throw new ApiError('No BOM available yet', 404)
  return scan.bom
}

export async function rescan(repoId) {
  await delay(600)
  const state = load()
  const r = state.repos[Number(repoId)]
  if (!r?.prMergedAt) throw new ApiError('Workflow PR must be merged before scanning', 409)
  if (r.scans[0]?.status === 'running') throw new ApiError('A scan is already running', 409)
  r.scans.unshift({ id: sha().slice(0, 10), status: 'running', trigger: 'workflow_dispatch', startedAt: now(), commit: sha() })
  save(state)
}
