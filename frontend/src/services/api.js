/**
 * MACSS — API Service Layer
 * All communication with the FastAPI backend goes through this module.
 * Components import from here, never hardcode URLs.
 */
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
})

// ── System ─────────────────────────────────────────────────────
export const getHealth = () => api.get('/api/health')

// ── Agents ─────────────────────────────────────────────────────
export const getAgents = () => api.get('/api/agents')

// ── Events ─────────────────────────────────────────────────────
export const getEvents = (limit = 50) => api.get('/api/events', { params: { limit } })

// ── Alerts ─────────────────────────────────────────────────────
export const getAlerts = (limit = 50) => api.get('/api/alerts', { params: { limit } })

// ── Decisions ──────────────────────────────────────────────────
export const getDecisions = (limit = 50) => api.get('/api/decisions', { params: { limit } })

// ── Actions ────────────────────────────────────────────────────
export const getActions = (limit = 50) => api.get('/api/actions', { params: { limit } })

// ── Simulation ─────────────────────────────────────────────────
export const getSimulationStatus = () => api.get('/api/simulation/status')
export const startSimulation = (config) => api.post('/api/simulation/start', config)
export const stopSimulation = () => api.post('/api/simulation/stop')
export const resetSimulation = () => api.post('/api/simulation/reset')

// ── Metrics ────────────────────────────────────────────────────
export const getMetrics = () => api.get('/api/metrics')

// ── Experiments ────────────────────────────────────────────────
export const getExperiments = () => api.get('/api/experiments')
export const runExperiment = (config) => api.post('/api/experiments/run', config)
export const getExperimentResults = (id) => api.get(`/api/experiments/${id}/results`)

export default api
