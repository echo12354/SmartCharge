import type {
  AcceptanceEvent,
  AcceptanceRunResult,
  AdminQueueCar,
  ApiResponse,
  Bill,
  ChargingPile,
  ChargingRequest,
  ChargingSession,
  DispatchOverview,
  ReportRow,
  StationSnapshot,
  User,
  UserVehicleOverview,
} from './types'

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
const JSON_HEADERS = { 'Content-Type': 'application/json' }
const AUTH_STORAGE_KEY = 'smartcharge_user'

let currentUsername: string | null = null

export function setApiUsername(username: string | null) {
  currentUsername = username
}

function loadStoredUsername(): string | null {
  const raw = localStorage.getItem(AUTH_STORAGE_KEY)
  if (!raw) return null

  try {
    const storedUser = JSON.parse(raw) as { username?: unknown }
    return typeof storedUser.username === 'string' && storedUser.username.trim()
      ? storedUser.username
      : null
  } catch {
    return null
  }
}

function normalizeErrorMessage(message: string | undefined, status: number): string {
  if (message === 'authentication required') {
    return '登录状态已失效，请重新登录'
  }

  return message || `璇锋眰澶辫触 (${status})`
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  username?: string | null,
): Promise<T> {
  const headers: Record<string, string> = {
    ...JSON_HEADERS,
    ...(options.headers as Record<string, string> | undefined),
  }
  const effectiveUser = username ?? currentUsername ?? loadStoredUsername()
  if (effectiveUser) {
    headers['X-Username'] = effectiveUser
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers })
  const contentType = response.headers.get('content-type') ?? ''
  if (!contentType.includes('application/json')) {
    throw new Error(`接口返回非 JSON (${response.status})：${path}`)
  }

  const body = (await response.json()) as ApiResponse<T> & { type?: string }

  if (!response.ok || body.success === false) {
    throw new Error(normalizeErrorMessage(body.message, response.status))
  }

  return (body.data ?? body) as T
}

export const api = {
  login(username: string, password: string): Promise<User> {
    return request<User>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    })
  },

  register(username: string, password: string, role = 'user'): Promise<User> {
    return request<User>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password, role }),
    })
  },

  listRequests(username: string): Promise<{ requests: ChargingRequest[]; total: number; maxAllowed: number }> {
    return request(`/api/charging-requests?userId=${encodeURIComponent(username)}`, {}, username)
  },

  submitRequest(
    username: string,
    chargeMode: string,
    amount: number,
    vehicleLabel: string,
    batteryCapacity?: number | null,
  ): Promise<ChargingRequest> {
    return request<ChargingRequest>('/api/charging-requests', {
      method: 'POST',
      body: JSON.stringify({ chargeMode, amount, vehicleLabel, batteryCapacity }),
    }, username)
  },

  modifyAmount(username: string, requestId: string, amount: number): Promise<ChargingRequest> {
    return request<ChargingRequest>('/api/charging-requests/amount', {
      method: 'PATCH',
      body: JSON.stringify({ requestId, amount }),
    }, username)
  },

  modifyMode(username: string, requestId: string, chargeMode: string): Promise<ChargingRequest> {
    return request<ChargingRequest>('/api/charging-requests/mode', {
      method: 'PATCH',
      body: JSON.stringify({ requestId, chargeMode }),
    }, username)
  },

  cancelRequest(username: string, requestId: string): Promise<ChargingRequest> {
    return request<ChargingRequest>('/api/charging-requests/cancel', {
      method: 'POST',
      body: JSON.stringify({ requestId }),
    }, username)
  },

  getUserVehicles(username: string): Promise<UserVehicleOverview> {
    return request<UserVehicleOverview>(
      `/api/charging-requests/car-state?userId=${encodeURIComponent(username)}`,
      {},
      username,
    )
  },

  dispatch(): Promise<unknown> {
    return request('/api/scheduling/dispatch', { method: 'POST' })
  },

  endCharging(sessionId: string, reason = '用户主动停止'): Promise<{ session: ChargingSession; bill: Bill }> {
    return request(`/api/charging-sessions/${sessionId}/end`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    })
  },

  getUserBills(username: string): Promise<{ bills: Bill[]; total: number }> {
    return request(`/api/bills?userId=${encodeURIComponent(username)}`, {}, username)
  },

  getAllBills(): Promise<{ bills: Bill[]; total: number }> {
    return request('/api/bills')
  },

  getPiles(): Promise<{ piles: ChargingPile[] }> {
    return request('/api/piles')
  },

  getAdminPiles(): Promise<{ piles: ChargingPile[] }> {
    return request('/api/admin/piles')
  },

  getPileDetail(pileId: number): Promise<Record<string, unknown>> {
    return request(`/api/admin/piles/${pileId}/details`)
  },

  powerOffPile(pileId: string, strategy = 'priority'): Promise<unknown> {
    return request(`/api/piles/${pileId}/power-off`, {
      method: 'POST',
      body: JSON.stringify({ reason: '管理员手动关闭', strategy }),
    })
  },

  reportFault(pileId: string, strategy = 'priority'): Promise<unknown> {
    return request(`/api/faults/${pileId}`, {
      method: 'POST',
      body: JSON.stringify({ reason: '充电桩故障', strategy }),
    })
  },

  recoverPile(pileId: string): Promise<unknown> {
    return request(`/api/faults/${pileId}/recover`, { method: 'POST' })
  },

  getAdminQueue(): Promise<{ cars: AdminQueueCar[] }> {
    return request('/api/admin/queue')
  },

  getReports(timeRange: string): Promise<{ reports: ReportRow[] }> {
    return request(`/api/admin/reports?timeRange=${timeRange}`)
  },

  getPileStatistics(): Promise<Record<string, unknown>> {
    return request('/api/admin/statistics/piles')
  },

  getDispatchOverview(): Promise<DispatchOverview> {
    return request('/api/admin/dispatch/overview')
  },

  getAdminSessions(): Promise<{ sessions: ChargingSession[]; totalCount: number }> {
    return request('/api/admin/charging/sessions')
  },

  getStationSnapshot(strategy = 'priority'): Promise<StationSnapshot> {
    return request(`/api/acceptance/snapshot?strategy=${encodeURIComponent(strategy)}`)
  },

  resetAcceptance(): Promise<unknown> {
    return request('/api/acceptance/reset', { method: 'POST' })
  },

  runAcceptanceAll(stopAt = '09:30', strategy = 'priority'): Promise<AcceptanceRunResult> {
    return request('/api/acceptance/run-all', {
      method: 'POST',
      body: JSON.stringify({ stopAt, strategy }),
    })
  },

  runAcceptanceNext(strategy = 'priority'): Promise<Record<string, unknown>> {
    return request('/api/acceptance/events/next', {
      method: 'POST',
      body: JSON.stringify({ strategy }),
    })
  },

  runAcceptanceEvent(index: number, strategy = 'priority'): Promise<Record<string, unknown>> {
    return request(`/api/acceptance/events/${index}`, {
      method: 'POST',
      body: JSON.stringify({ strategy }),
    })
  },

  listAcceptanceEvents(): Promise<{ events: AcceptanceEvent[]; total: number }> {
    return request('/api/acceptance/events')
  },
}
