import { FormEvent, useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'
import type { UserVehicleOverview } from '../../api/types'
import VehicleCard from '../../components/VehicleCard'
import { useAuth } from '../../contexts/AuthContext'

export default function UserHome() {
  const { user } = useAuth()
  const username = user!.username

  const [overview, setOverview] = useState<UserVehicleOverview | null>(null)
  const [chargeMode, setChargeMode] = useState<'fast' | 'slow'>('fast')
  const [amount, setAmount] = useState(30)
  const [batteryCapacity, setBatteryCapacity] = useState(60)
  const [vehicleLabel, setVehicleLabel] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

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

  const canAddVehicle = (overview?.totalActive ?? 0) < (overview?.maxAllowed ?? 10)

  async function handleSubmitRequest(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError('')
    setMessage('')
    try {
      await api.submitRequest(username, chargeMode, amount, vehicleLabel.trim(), batteryCapacity)
      setVehicleLabel('')
      await refresh()
      setMessage('新的充电请求已提交')
    } catch (err) {
      setError(err instanceof Error ? err.message : '提交失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-grid">
      <section className="card hero-card">
        <div>
          <p className="eyebrow">我的车辆</p>
          <h2>{overview?.totalActive ?? 0} / {overview?.maxAllowed ?? 10} 辆在排队或充电</h2>
          <p className="muted">同一账号可管理多辆车，每辆车对应一条独立充电请求与排队号。</p>
        </div>
      </section>

      {message && <div className="alert alert-success">{message}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      {canAddVehicle && (
        <section className="card">
          <h3>添加充电请求</h3>
          <form className="form inline-form" onSubmit={handleSubmitRequest}>
            <label>
              车辆名称
              <input
                value={vehicleLabel}
                onChange={(e) => setVehicleLabel(e.target.value)}
                placeholder="例如：家庭 SUV / 通勤车"
              />
            </label>
            <label>
              充电模式
              <select value={chargeMode} onChange={(e) => setChargeMode(e.target.value as 'fast' | 'slow')}>
                <option value="fast">快充 (F 号)</option>
                <option value="slow">慢充 (T 号)</option>
              </select>
            </label>
            <label>
              请求充电量 (度)
              <input type="number" min={1} value={amount} onChange={(e) => setAmount(Number(e.target.value))} required />
            </label>
            <label>
              电池总容量（度）
              <input type="number" min={1} value={batteryCapacity} onChange={(e) => setBatteryCapacity(Number(e.target.value))} required />
            </label>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              提交请求
            </button>
          </form>
        </section>
      )}

      {!canAddVehicle && (
        <div className="alert alert-error">
          已达到活跃请求上限（{overview?.maxAllowed} 辆），请先完成或取消现有请求后再添加。
        </div>
      )}

      <section className="vehicle-list">
        {(overview?.vehicles ?? []).length === 0 ? (
          <section className="card">
            <p className="muted">暂无进行中的充电请求，请为车辆提交第一条充电请求。</p>
          </section>
        ) : (
          overview!.vehicles.map((vehicle, index) => (
            <VehicleCard
              key={vehicle.request?.requestId ?? vehicle.chargingSession?.sessionId ?? `${vehicle.state}-${index}`}
              username={username}
              vehicle={vehicle}
              onUpdated={refresh}
            />
          ))
        )}
      </section>

      <section className="card info-card">
        <h3>多客户端说明</h3>
        <p className="muted">
          前端与后端已分离：可在不同浏览器、不同电脑打开同一前端地址，登录同一账号即可同步查看所有车辆状态。
          后端地址通过 <code>frontend/.env</code> 中的 <code>VITE_API_BASE_URL</code> 配置。
        </p>
      </section>
    </div>
  )
}
