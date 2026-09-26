import { request } from './client'

export const signup = (email, password) =>
  request('/auth/signup', { method: 'POST', body: { email, password }, auth: false })

export const login = (email, password) =>
  request('/auth/login', { method: 'POST', body: { email, password }, auth: false })
