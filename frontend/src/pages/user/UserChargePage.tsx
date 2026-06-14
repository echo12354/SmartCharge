import { FormEvent, useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'
import type { UserVehicleOverview } from '../../api/types'
import { useAuth } from '../../contexts/AuthContext'

export default function UserChargePage() {
  const { user } = useAuth()
  const username = user!.username

  const [overview, setOverview] = useState<UserVehicleOverview | null>(null)
  const [chargeMode, setChargeMode] = useState<'fast' | 'slow'>('fast')
  const [amount, setAmount] = useState(30)
  const [batteryCapacity, setBatteryCapacity] = useState<number | ''>(120)
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
  }, [refresh])

  const canAddVehicle = (overview?.totalActive ?? 0) < (overview?.maxAllowed ?? 10)

  async function handleSubmitRequest(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError('')
    setMessage('')
    try {
      await api.submitRequest(
        username,
        chargeMode,
        amount,
        vehicleLabel.trim(),
        batteryCapacity === '' ? 120 : Number(batteryCapacity),
      )
      setVehicleLabel('')
      setBatteryCapacity(120)
      await refresh()
      setMessage('新的充电请求已提交')
    } catch (err) {
      const message = err instanceof Error ? err.message : '提交失败'
      setError(message.includes('waiting queue is full') ? '等候区已满，请稍后再试' : message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-grid">
      <section className="card hero-card compact">
        <div>
          <p className="eyebrow">预约充电</p>
          <h2>提交新的充电请求</h2>
          <p className="muted">选择快充或慢充，填写本次所需电量，系统会自动生成排队号。</p>
        </div>
      </section>

      {message && <div className="alert alert-success">{message}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      {canAddVehicle ? (
        <section className="card">
          <h3>新增充电请求</h3>
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
              车辆电池总容量 (度)
              <input
                type="number"
                min={1}
                value={batteryCapacity}
                onChange={(e) => setBatteryCapacity(e.target.value === '' ? '' : Number(e.target.value))}
                placeholder="例如：75"
              />
            </label>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              提交请求
            </button>
          </form>
        </section>
      ) : (
        <div className="alert alert-error">
          已达到活跃请求上限（{overview?.maxAllowed} 辆），请先完成或取消现有请求后再添加。
        </div>
      )}
    </div>
  )
}
