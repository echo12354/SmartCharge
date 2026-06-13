import { STATION_COLUMNS } from '../utils/pileLabels'

interface StationSnapshot {
  simTime?: string
  piles: Record<string, string>
  waitingArea: string
  clock?: { enabled?: boolean; displayTime?: string }
}

interface ChargingStationBoardProps {
  snapshot: StationSnapshot | null
  title?: string
}

export default function ChargingStationBoard({ snapshot, title = '充电区状态（验收表格式）' }: ChargingStationBoardProps) {
  if (!snapshot) {
    return <p className="muted">加载充电区状态...</p>
  }

  const timeLabel = snapshot.clock?.enabled
    ? `模拟时刻 ${snapshot.simTime}`
    : `当前时刻 ${snapshot.simTime}`

  return (
    <div className="station-board">
      <div className="station-board-head">
        <h3>{title}</h3>
        <span className="muted">{timeLabel}</span>
      </div>
      <div className="station-grid">
        {STATION_COLUMNS.map((col) => (
          <div key={col.pileId} className="station-cell">
            <div className="station-cell-title">{col.label}</div>
            <div className="station-cell-sub">{col.alias} · 桩 {col.pileId}</div>
            <div className="station-cell-body">{snapshot.piles[col.label] || '-'}</div>
          </div>
        ))}
        <div className="station-cell waiting-cell">
          <div className="station-cell-title">等候区</div>
          <div className="station-cell-sub">容量 10 辆</div>
          <div className="station-cell-body">{snapshot.waitingArea || '-'}</div>
        </div>
      </div>
      <p className="muted station-hint">
        充电中：(车号, 已充电量, 当前费用)；排队中：(车号, 模式, 请求电量)，多车用「-」连接。
      </p>
    </div>
  )
}
