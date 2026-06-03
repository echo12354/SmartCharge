import type {
  AdminQueueCar,
  ApiResponse,
  Bill,
  ChargingPile,
  ChargingRequest,
  ChargingSession,
  ReportRow,
  User,
  UserVehicleOverview,
} from './types'

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
const JSON_HEADERS = { 'Content-Type': 'application/json' }

async function request<T>(
  path: string,
  options: RequestInit = {},
  username?: string | null,
): Promise<T> {
  const headers: Record<string, string> = {
    ...JSON_HEADERS,
    ...(options.headers as Record<string, string> | undefined),
  }
  if (username) {
    headers['X-Username'] = username
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers })
  const body = (await response.json()) as ApiResponse<T> & { type?: string }

  if (!response.ok || body.success === false) {
    throw new Error(body.message || `请求失败 (${response.status})`)
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
  ): Promise<ChargingRequest> {
    return request<ChargingRequest>('/api/charging-requests', {
      method: 'POST',
      body: JSON.stringify({ chargeMode, amount, vehicleLabel }),
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

  powerOnPile(pileId: string): Promise<unknown> {
    return request(`/api/piles/${pileId}/power-on`, { method: 'POST' })
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
}
