import type { AdminQueueCar, ChargingPile, ChargingSession } from '../api/types'
import StatusBadge, { formatMode } from './StatusBadge'
import { PILE_LABELS, STATION_COLUMNS, SYSTEM_CONFIG } from '../utils/pileLabels'

interface ChargingStationOverviewProps {
  piles?: ChargingPile[]
  cars: AdminQueueCar[]
  sessions: ChargingSession[]
  title?: string
  compact?: boolean
}

function pileEnabled(pile: ChargingPile) {
  return pile.isEnabled ?? pile.isActive ?? pile.status !== 'FAULT'
}

function pileStatusTone(status: string, enabled: boolean) {
  if (!enabled || status === 'FAULT' || status === 'OFFLINE') return 'danger'
  if (status === 'CHARGING') return 'success'
  return 'default'
}

function findSession(car: AdminQueueCar, sessions: ChargingSession[]) {
  return sessions.find((item) => (
    car.requestId
      ? item.requestId === car.requestId
      : item.userId === car.userId && item.pileId === car.pileName
  ))
}

export default function ChargingStationOverview({
  piles = [],
  cars,
  sessions,
  title = '充电区实时状态',
  compact = false,
}: ChargingStationOverviewProps) {
  const waitingCars = cars.filter((car) => car.pileName === '等待区')
  const pileMap = new Map(piles.map((pile) => [pile.pileId, pile]))

  return (
    <div className="overview-board">
      <div className="overview-board-head">
        <h3>{title}</h3>
        <span className="muted">
          等候区 {waitingCars.length}/{SYSTEM_CONFIG.waitingCapacity} · 每桩队列最多 {SYSTEM_CONFIG.pileQueueCapacity} 辆
        </span>
      </div>

      <div className={`overview-pile-grid ${compact ? 'compact' : ''}`}>
        {STATION_COLUMNS.map((col) => {
          const pile = pileMap.get(col.pileId)
          const pileCars = cars.filter((car) => car.pileName === col.pileId)
          const chargingCar = pileCars.find((car) => car.statusClass === 'charging')
          const queueCars = pileCars.filter((car) => car.statusClass !== 'charging')
          const enabled = pile ? pileEnabled(pile) : true
          const status = pile?.status ?? (chargingCar ? 'CHARGING' : 'IDLE')
          const session = chargingCar ? findSession(chargingCar, sessions) : undefined

          return (
            <article
              key={col.pileId}
              className={`overview-pile-card ${enabled ? '' : 'overview-pile-offline'}`}
            >
              <div className="overview-pile-head">
                <div>
                  <strong>{PILE_LABELS[col.pileId] || col.label}</strong>
                  <span className="overview-pile-meta">
                    {formatMode(col.pileId === 'A' || col.pileId === 'B' ? 'fast' : 'slow')}
                    {' · '}
                    {pile?.power ?? (col.pileId === 'A' || col.pileId === 'B' ? 30 : 10)} 度/时
                  </span>
                </div>
                <StatusBadge
                  value={enabled ? status : 'OFFLINE'}
                  tone={pileStatusTone(status, enabled)}
                />
              </div>

              <div className="overview-slot overview-slot-charging">
                <span className="overview-slot-label">正在充电</span>
                {!chargingCar ? (
                  <p className="overview-empty">暂无车辆</p>
                ) : (
                  <div className="overview-car-block">
                    <div className="overview-car-title">
                      <span>{chargingCar.vehicleLabel || chargingCar.userId}</span>
                      <span>{formatMode(chargingCar.chargeMode)}</span>
                    </div>
                    {session ? (
                      <>
                        <div className="overview-progress-row">
                          <span>{session.currentAmount.toFixed(2)} / {chargingCar.requestedCharge} 度</span>
                          <span>{session.progressPercent.toFixed(1)}%</span>
                        </div>
                        <div className="overview-progress-bar">
                          <div
                            className="overview-progress-fill"
                            style={{ width: `${Math.min(100, session.progressPercent)}%` }}
                          />
                        </div>
                      </>
                    ) : (
                      <p className="overview-car-detail">目标 {chargingCar.requestedCharge} 度 · {chargingCar.queueTime}</p>
                    )}
                  </div>
                )}
              </div>

              <div className="overview-slot">
                <span className="overview-slot-label">桩内排队 ({queueCars.length}/{SYSTEM_CONFIG.pileQueueCapacity - 1})</span>
                {queueCars.length === 0 ? (
                  <p className="overview-empty">无排队车辆</p>
                ) : (
                  <ul className="overview-queue-list">
                    {queueCars.map((car, index) => (
                      <li key={`${car.pileName}-${car.requestId}-${index}`}>
                        <span>{index + 1}. {car.vehicleLabel || car.userId}</span>
                        <span>{formatMode(car.chargeMode)} · {car.requestedCharge} 度</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </article>
          )
        })}
      </div>

      <section className="overview-waiting-panel">
        <div className="overview-waiting-head">
          <strong>等候区</strong>
          <span className="muted">{waitingCars.length} / {SYSTEM_CONFIG.waitingCapacity} 辆</span>
        </div>
        {waitingCars.length === 0 ? (
          <p className="overview-empty">等候区暂无车辆，新请求将按到达顺序排队。</p>
        ) : (
          <ul className="overview-waiting-list">
            {waitingCars.map((car, index) => (
              <li key={`wait-${car.requestId}-${index}`}>
                <span className="overview-waiting-no">{index + 1}</span>
                <div className="overview-waiting-body">
                  <strong>{car.vehicleLabel || car.userId}</strong>
                  <span>{formatMode(car.chargeMode)} · 需 {car.requestedCharge} 度 · 已等 {car.queueTime}</span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
