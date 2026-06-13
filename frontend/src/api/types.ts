export interface ApiResponse<T = unknown> {
  success: boolean
  message: string
  data?: T
}

export interface User {
  username: string
  role: string
  type?: string
  createdAt?: string
  lastLogin?: string
}

export interface ChargingRequest {
  requestId: string
  userId: string
  vehicleLabel?: string
  chargeMode: string
  requestedAmount: number
  status: string
  queueNumber: string
  assignedPileId: string | null
  createdAt: string
  updatedAt: string
}

export interface ChargingSession {
  sessionId: string
  userId: string
  pileId: string
  targetAmount: number
  currentAmount: number
  pilePower: number
  status: string
  progressPercent: number
  requestId?: string | null
  startTime: string | null
  endTime: string | null
  durationHours: number
  remainingHours: number
  stopReason: string | null
}

export interface Bill {
  billId: string
  sessionId: string
  userId: string
  pileId: string
  energyAmount: number
  startTime: string
  endTime: string
  durationHours: number
  priceType: string
  unitPrice: number
  chargeFee: number
  serviceFee: number
  totalFee: number
  status: string
  createdAt: string
}

export interface CarState {
  request: ChargingRequest | null
  waitingCar: Record<string, unknown> | null
  pileQueue: {
    pileId: string
    queuePosition: string
    queueNumber?: string
    requestId?: string
  } | null
  chargingSession: ChargingSession | null
  state: string
  aheadCount?: number
}

export interface VehicleState extends CarState {}

export interface UserVehicleOverview {
  vehicles: VehicleState[]
  totalActive: number
  maxAllowed: number
  request?: ChargingRequest | null
  state?: string
}

export interface ChargingPile {
  pileId: string
  pileType: string
  power: number
  status: string
  isEnabled: boolean
  totalSessions: number
  totalEnergy: number
  totalHours: number
  currentSessionId: string | null
  id?: number
  name?: string
  isActive?: boolean
  queueCount?: number
}

export interface AdminQueueCar {
  id: number
  pileName: string
  userId: string
  requestId?: string
  vehicleLabel?: string
  chargeMode?: string
  requestedCharge: number
  queueTime: string
  status: string
  statusClass: string
}

export interface StationSnapshot {
  simTime: string
  piles: Record<string, string>
  waitingArea: string
  clock?: {
    enabled?: boolean
    displayTime?: string
    currentTime?: string
    timeScale?: number
  }
  lastEventIndex?: number
}

export interface DispatchOverview {
  engineStatus: {
    isRunning: boolean
    totalDispatched: number
  }
  pileQueues: Array<{
    pileId: string
    chargingCar: Record<string, unknown> | null
    waitingCar: Record<string, unknown> | null
    waitingCars?: Array<Record<string, unknown>>
    capacity: number
    availableCapacity: number
  }>
  utilizationSummary: Record<string, number>
  recentDecisions: Array<Record<string, unknown>>
}

export interface AcceptanceEvent {
  index: number
  simTime: string
  event: string
}

export interface AcceptanceRunResult {
  executed: number
  stopAt: string
  results: Array<{
    index: number
    simTime: string
    event: string
    snapshot: StationSnapshot
  }>
  finalSnapshot: StationSnapshot
}

export interface ReportRow {
  id: number
  pileId: string
  pileName: string
  timeRange: string
  chargeCount: number
  chargeDuration: number
  energyAmount: number
  chargeFee: number
  serviceFee: number
  totalFee: number
}

export interface PileQueueInfo {
  pileId: string
  chargingCar: Record<string, unknown> | null
  waitingCar: Record<string, unknown> | null
  capacity: number
}
