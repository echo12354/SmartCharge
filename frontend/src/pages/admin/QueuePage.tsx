import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import type { AdminQueueCar } from '../../api/types'
import StatusBadge, { formatMode } from '../../components/StatusBadge'
import { PILE_LABELS, pileChargeMode } from '../../utils/pileLabels'

export default function QueuePage() {
  const [cars, setCars] = useState<AdminQueueCar[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const load = useCallback(() => api.getAdminQueue()
    .then((result) => setCars(result.cars))
    .catch((err) => setError(err instanceof Error ? err.message : '加载失败'))
    .finally(() => setLoading(false)), [])

  useEffect(() => {
    load()
    const timer = window.setInterval(load, 5000)
    return () => window.clearInterval(timer)
  }, [load])

  const waitingCount = cars.filter((car) => car.pileName === '等待区').length

  return (
    <div className="page-grid">
      <section className="card hero-card compact">
        <div>
          <p className="eyebrow">队列列表</p>
          <h2>等候服务车辆</h2>
          <p className="muted">按位置列出所有排队车辆；可视化充电区请查看「充电区监控」。</p>
        </div>
        <div className="hero-meta">
          <span>总车辆：<strong>{cars.length}</strong></span>
          <span>等候区：<strong>{waitingCount}</strong></span>
          <Link to="/admin/monitor" className="btn btn-secondary">充电区视图</Link>
        </div>
      </section>

      {error && <div className="alert alert-error">{error}</div>}

      <section className="card table-card">
        {loading ? (
          <p className="muted">加载中...</p>
        ) : cars.length === 0 ? (
          <p className="muted">当前没有排队车辆。</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>序号</th>
                  <th>位置</th>
                  <th>用户 ID</th>
                  <th>车辆电池总容量 (度)</th>
                  <th>充电模式</th>
                  <th>请求充电量 (度)</th>
                  <th>排队时长</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                {cars.map((car) => (
                  <tr key={`${car.pileName}-${car.userId}-${car.id}`}>
                    <td>{car.id}</td>
                    <td>{car.pileName === '等待区' ? '等候区' : (PILE_LABELS[car.pileName] || car.pileName)}</td>
                    <td>{car.userId}</td>
                    <td>{car.batteryCapacity ?? '-'}</td>
                    <td>{formatMode(car.chargeMode || pileChargeMode(car.pileName) || undefined)}</td>
                    <td>{car.requestedCharge}</td>
                    <td>{car.queueTime}</td>
                    <td>
                      <StatusBadge
                        value={car.statusClass === 'charging' ? 'CHARGING' : 'WAITING'}
                        tone={car.statusClass === 'charging' ? 'success' : 'warning'}
                      />
                      <span className="status-text">{car.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
