import { request } from './client'
import * as mock from './mock'

export const USE_MOCKS = import.meta.env.VITE_USE_MOCKS !== 'false'

const real = {
  getInstallation: () => request('/github/installation'),
  connectGitHub: () => request('/github/install-url').then(({ url }) => (window.location.href = url)),
  completeInstallation: (installationId, state) =>
    request('/github/installation', { method: 'POST', body: { installation_id: Number(installationId), state } }),
  disconnectGitHub: () => request('/github/installation', { method: 'DELETE' }),
  listRepos: () => request('/repos'),
  getUsage: () => request('/usage'),
  enableRepos: (ids) => request('/repos/enable', { method: 'POST', body: { repo_ids: ids } }),
  disableRepo: (id) => request(`/repos/${id}/enable`, { method: 'DELETE' }),
  getRepo: (id) => request(`/repos/${id}`),
  getBom: (repoId, scanId) => request(scanId ? `/repos/${repoId}/scans/${scanId}/bom` : `/repos/${repoId}/bom`),
  rescan: (id) => request(`/repos/${id}/scans`, { method: 'POST' }),
}

const api = USE_MOCKS ? mock : real

export const {
  getInstallation,
  connectGitHub,
  completeInstallation,
  disconnectGitHub,
  listRepos,
  getUsage,
  enableRepos,
  disableRepo,
  getRepo,
  getBom,
  rescan,
} = api
