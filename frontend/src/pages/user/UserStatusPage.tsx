import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'
import type { UserVehicleOverview } from '../../api/types'
import VehicleCard from '../../components/VehicleCard'
import { useAuth } from '../../contexts/AuthContext'

export default function UserStatusPage() {
  const { user } = useAuth()
  const username = user!.username

  const [overview, setOverview] = useState<UserVehicleOverview | null>(null)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    const data = await api.getUserVehicles(username)
    setOverview(data)
  }, [username])

  useEffect(() => {
    refresh().catch((err) => setError(err instanceof Error ? err.message : '加载失败'))
    const timer = window.setInterval(() => {
      refresh().catch(() => undefined)
    }, 5000)
    return () => window.clearInterval(timer)
  }, [refresh])

  return (
    <div className="page-grid">
      <section className="card hero-card compact">
        <div>
          <p className="eyebrow">充电状态</p>
          <h2>{overview?.totalActive ?? 0} / {overview?.maxAllowed ?? 10} 辆在排队或充电</h2>
          <p className="muted">查看当前车辆状态、排队信息、充电进度，并处理修改、取消或结束充电。</p>
        </div>
      </section>

      {error && <div className="alert alert-error">{error}</div>}

      <section className="vehicle-list">
        {(overview?.vehicles ?? []).length === 0 ? (
          <section className="card">
            <p className="muted">暂无进行中的充电请求，请先前往预约充电页面提交请求。</p>
          </section>
        ) : (
          overview!.vehicles.map((vehicle) => (
            <VehicleCard
              key={vehicle.request!.requestId}
              username={username}
              vehicle={vehicle}
              onUpdated={refresh}
            />
          ))
        )}
      </section>
    </div>
  )
}
