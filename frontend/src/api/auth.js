import { api } from './client'

export function login(email, password) {
  return api.post('/auth/login', { email, password }).then((r) => r.data)
}

export function register({ email, password, full_name, firm_name }) {
  return api.post('/auth/register', { email, password, full_name, firm_name }).then((r) => r.data)
}

export function getMe() {
  return api.get('/auth/me').then((r) => r.data)
}

export function logout() {
  return api.post('/auth/logout').then((r) => r.data)
}
