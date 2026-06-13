import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'
import type { AdminQueueCar, ChargingPile, ChargingSession } from '../../api/types'
import ChargingStationOverview from '../../components/ChargingStationOverview'
import StatusBadge, { formatMode } from '../../components/StatusBadge'
import { PILE_LABELS, pileChargeMode } from '../../utils/pileLabels'

export default function MonitorPage() {
  const [cars, setCars] = useState<AdminQueueCar[]>([])
  const [piles, setPiles] = useState<ChargingPile[]>([])
  const [sessions, setSessions] = useState<ChargingSession[]>([])
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    const [pileData, queueData, sessionData] = await Promise.all([
      api.getAdminPiles(),
      api.getAdminQueue(),
      api.getAdminSessions(),
    ])
    setPiles(pileData.piles)
    setCars(queueData.cars)
    setSessions(sessionData.sessions)
  }, [])

  useEffect(() => {
    refresh().catch((err) => setError(err instanceof Error ? err.message : '加载失败'))
    const timer = window.setInterval(() => refresh().catch(() => undefined), 4000)
    return () => window.clearInterval(timer)
  }, [refresh])

  const waitingCars = cars.filter((car) => car.pileName === '等待区')
  const pileCars = cars.filter((car) => car.pileName !== '等待区')

  return (
    <div className="page-grid">
      <section className="card hero-card compact">
        <div>
          <p className="eyebrow">充电区监控</p>
          <h2>充电桩与队列状态</h2>
          <p className="muted">查看各桩充电进度、桩内排队与等候区车辆，数据每 4 秒自动刷新。</p>
        </div>
        <div className="hero-meta">
          <span>等候区：<strong>{waitingCars.length}</strong></span>
          <span>充电区车辆：<strong>{pileCars.length}</strong></span>
          <span>活跃会话：<strong>{sessions.length}</strong></span>
        </div>
      </section>

      {error && <div className="alert alert-error">{error}</div>}

      <section className="card">
        <ChargingStationOverview
          piles={piles}
          cars={cars}
          sessions={sessions}
        />
      </section>

      <section className="card table-card">
        <h3>充电区明细列表</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>充电桩</th>
                <th>用户</th>
                <th>模式</th>
                <th>请求电量</th>
                <th>已充电量</th>
                <th>进度</th>
                <th>排队时长</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              {pileCars.length === 0 ? (
                <tr><td colSpan={8} className="muted">充电区暂无车辆</td></tr>
              ) : pileCars.map((car) => {
                const session = sessions.find((item) => (
                  car.requestId
                    ? item.requestId === car.requestId
                    : item.userId === car.userId && item.pileId === car.pileName
                ))
                const mode = car.chargeMode || pileChargeMode(car.pileName) || session?.pileId && pileChargeMode(session.pileId)
                return (
                  <tr key={`${car.pileName}-${car.userId}-${car.id}`}>
                    <td>{PILE_LABELS[car.pileName] || car.pileName}</td>
                    <td>{car.vehicleLabel || car.userId}</td>
                    <td>{formatMode(mode || undefined)}</td>
                    <td>{car.requestedCharge} 度</td>
                    <td>{session ? `${session.currentAmount} 度` : '-'}</td>
                    <td>{session ? `${session.progressPercent}%` : '-'}</td>
                    <td>{car.queueTime}</td>
                    <td>
                      <StatusBadge
                        value={car.statusClass === 'charging' ? 'CHARGING' : 'WAITING'}
                        tone={car.statusClass === 'charging' ? 'success' : 'warning'}
                      />
                      <span className="status-text">{car.status}</span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
