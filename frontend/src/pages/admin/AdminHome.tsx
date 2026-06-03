import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'

interface Stats {
  activePiles?: number
  totalPiles?: number
  chargingPiles?: number
  offlinePiles?: number
  totalQueuedCars?: number
  totalRevenue?: number
}

export default function AdminHome() {
  const [stats, setStats] = useState<Stats>({})
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    const data = await api.getPileStatistics()
    setStats(data as Stats)
  }, [])

  useEffect(() => {
    refresh().catch((err) => setError(err instanceof Error ? err.message : '加载失败'))
    const timer = window.setInterval(() => refresh().catch(() => undefined), 8000)
    return () => window.clearInterval(timer)
  }, [refresh])

  async function triggerDispatch() {
    setError('')
    setMessage('')
    try {
      await api.dispatch()
      await refresh()
      setMessage('调度已完成，等候区车辆已按最短完成时间策略分配至充电桩')
    } catch (err) {
      setError(err instanceof Error ? err.message : '调度失败')
    }
  }

  return (
    <div className="page-grid">
      <section className="card hero-card">
        <div>
          <p className="eyebrow">系统概览</p>
          <h2>充电站运行状态</h2>
          <p className="muted">管理充电桩启停、查看队列与统计报表。调度策略：同模式下最短完成时间。</p>
        </div>
        <button type="button" className="btn btn-primary" onClick={triggerDispatch}>
          手动触发调度
        </button>
      </section>

      {message && <div className="alert alert-success">{message}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      <section className="metrics-grid">
        <div className="metric-card">
          <span>在线充电桩</span>
          <strong>{stats.activePiles ?? 0} / {stats.totalPiles ?? 5}</strong>
        </div>
        <div className="metric-card">
          <span>充电中</span>
          <strong>{stats.chargingPiles ?? 0}</strong>
        </div>
        <div className="metric-card">
          <span>等候区车辆</span>
          <strong>{stats.totalQueuedCars ?? 0}</strong>
        </div>
        <div className="metric-card">
          <span>累计收入</span>
          <strong>¥{(stats.totalRevenue ?? 0).toFixed(2)}</strong>
        </div>
      </section>

      <section className="card info-card">
        <h3>系统配置</h3>
        <div className="config-grid">
          <div><strong>快充桩</strong><span>A、B（30 度/小时）</span></div>
          <div><strong>慢充桩</strong><span>C、D、E（10 度/小时）</span></div>
          <div><strong>等候区容量</strong><span>6 个车位</span></div>
          <div><strong>桩队列长度</strong><span>每桩 2 位（1 充电 + 1 等待）</span></div>
        </div>
      </section>

      <section className="card">
        <h3>快捷入口</h3>
        <div className="quick-links">
          <a href="/admin/piles" className="quick-link">管理充电桩启停与故障</a>
          <a href="/admin/queue" className="quick-link">查看各区域等候车辆</a>
          <a href="/admin/reports" className="quick-link">查看日/周/月统计报表</a>
        </div>
      </section>
    </div>
  )
}
