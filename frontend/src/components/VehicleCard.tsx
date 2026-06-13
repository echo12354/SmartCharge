import { useState } from 'react'
import { api } from '../api/client'
import type { VehicleState } from '../api/types'
import StatusBadge, { formatMode } from './StatusBadge'

const STATE_LABELS: Record<string, string> = {
  IDLE: '空闲',
  WAITING_AREA: '等候区排队中',
  PILE_QUEUE: '充电桩队列等待',
  CHARGING: '正在充电',
  WAITING: '等候区',
  DISPATCHED: '已调度',
}

interface VehicleCardProps {
  username: string
  vehicle: VehicleState
  onUpdated: () => Promise<void>
}

export default function VehicleCard({ username, vehicle, onUpdated }: VehicleCardProps) {
  const request = vehicle.request
  const session = vehicle.chargingSession
  const [editAmount, setEditAmount] = useState(request?.requestedAmount ?? 1)
  const [editMode, setEditMode] = useState(request?.chargeMode ?? 'fast')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const label = request ? request.vehicleLabel || `车辆 ${request.queueNumber || request.requestId.slice(-4)}` : '暂无请求信息'
  const isWaiting = vehicle.state === 'WAITING_AREA'
  const isCharging = vehicle.state === 'CHARGING'
  const inPileQueue = vehicle.state === 'PILE_QUEUE'
  const isDispatched = vehicle.state === 'DISPATCHED'
  const canCancelQueue = Boolean(request) && !isCharging && (inPileQueue || isDispatched)

  async function runAction(action: () => Promise<unknown>) {
    setLoading(true)
    setError('')
    try {
      await action()
      await onUpdated()
    } catch (err) {
      setError(err instanceof Error ? err.message : '操作失败')
    } finally {
      setLoading(false)
    }
  }

  function runConfirmed(message: string, action: () => Promise<unknown>) {
    if (!window.confirm(message)) {
      return
    }
    void runAction(action)
  }

  return (
    <article className="card vehicle-card">
      <div className="vehicle-head">
        <div>
          <h3>{label}</h3>
          {request ? (
            <p className="muted">
              排队号 {request.queueNumber || '-'} · {formatMode(request.chargeMode)} · {request.requestedAmount} 度
            </p>
          ) : (
            <p className="muted">暂无请求信息</p>
          )}
        </div>
        <StatusBadge value={vehicle.state} tone={isCharging ? 'success' : 'warning'} />
      </div>

      <div className="vehicle-meta">
        <span>状态：{STATE_LABELS[vehicle.state] || vehicle.state}</span>
        {!isCharging && <span>前方等待：{vehicle.aheadCount ?? 0} 辆</span>}
        {vehicle.pileQueue?.pileId && <span>充电桩：{vehicle.pileQueue.pileId}</span>}
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {isWaiting && request && (
        <div className="vehicle-actions">
          <div className="inline-form">
            <label>
              模式
              <select value={editMode} onChange={(e) => setEditMode(e.target.value)}>
                <option value="fast">快充</option>
                <option value="slow">慢充</option>
              </select>
            </label>
            <label>
              电量
              <input type="number" min={1} value={editAmount} onChange={(e) => setEditAmount(Number(e.target.value))} />
            </label>
          </div>
          <div className="button-row">
            <button type="button" className="btn btn-secondary" disabled={loading} onClick={() => runConfirmed('确认修改本次请求充电量吗？', () => api.modifyAmount(username, request.requestId, editAmount))}>
              保存电量
            </button>
            <button type="button" className="btn btn-secondary" disabled={loading || editMode === request.chargeMode} onClick={() => runConfirmed('修改充电模式会重新排队，确认继续吗？', () => api.modifyMode(username, request.requestId, editMode))}>
              切换模式
            </button>
            <button type="button" className="btn btn-danger" disabled={loading} onClick={() => runConfirmed('确认取消本次充电请求吗？', () => api.cancelRequest(username, request.requestId))}>
              取消请求
            </button>
          </div>
        </div>
      )}

      {canCancelQueue && request && (
        <div className="button-row">
          <button type="button" className="btn btn-danger" disabled={loading} onClick={() => runConfirmed('确认取消本次充电请求吗？', () => api.cancelRequest(username, request.requestId))}>
            取消排队
          </button>
        </div>
      )}

      {isCharging && session && (
        <div className="vehicle-charging">
          <div className="progress-block">
            <div className="progress-head">
              <span>已充 {session.currentAmount} / {session.targetAmount} 度</span>
              <span>{session.progressPercent}%</span>
            </div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${session.progressPercent}%` }} />
            </div>
          </div>
          <button type="button" className="btn btn-primary" disabled={loading} onClick={() => runConfirmed('确认结束当前充电并生成详单吗？', () => api.endCharging(session.sessionId))}>
            结束充电
          </button>
        </div>
      )}
    </article>
  )
}
