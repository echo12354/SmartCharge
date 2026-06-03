import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import type { AdminQueueCar } from '../../api/types'
import StatusBadge from '../../components/StatusBadge'

export default function QueuePage() {
  const [cars, setCars] = useState<AdminQueueCar[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = () => api.getAdminQueue()
      .then((result) => setCars(result.cars))
      .catch((err) => setError(err instanceof Error ? err.message : '加载失败'))
      .finally(() => setLoading(false))

    load()
    const timer = window.setInterval(load, 5000)
    return () => window.clearInterval(timer)
  }, [])

  return (
    <div className="page-grid">
      <section className="card hero-card compact">
        <div>
          <p className="eyebrow">队列监控</p>
          <h2>等候服务车辆</h2>
          <p className="muted">展示等候区与各充电桩队列中的车辆信息。</p>
        </div>
        <div className="hero-meta">
          <span>当前车辆数：<strong>{cars.length}</strong></span>
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
                  <th>请求充电量 (度)</th>
                  <th>排队时长</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                {cars.map((car) => (
                  <tr key={`${car.pileName}-${car.userId}-${car.id}`}>
                    <td>{car.id}</td>
                    <td>{car.pileName}</td>
                    <td>{car.userId}</td>
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
