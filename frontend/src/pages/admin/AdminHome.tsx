import { Link } from 'react-router-dom'
import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'
import type { AdminQueueCar, ChargingPile, ChargingSession, DispatchOverview } from '../../api/types'
import ChargingStationOverview from '../../components/ChargingStationOverview'
import { SYSTEM_CONFIG } from '../../utils/pileLabels'

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
  const [overview, setOverview] = useState<DispatchOverview | null>(null)
  const [piles, setPiles] = useState<ChargingPile[]>([])
  const [cars, setCars] = useState<AdminQueueCar[]>([])
  const [sessions, setSessions] = useState<ChargingSession[]>([])
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    const [statsData, overviewData, pileData, queueData, sessionData] = await Promise.all([
      api.getPileStatistics(),
      api.getDispatchOverview(),
      api.getAdminPiles(),
      api.getAdminQueue(),
      api.getAdminSessions(),
    ])
    setStats(statsData as Stats)
    setOverview(overviewData)
    setPiles(pileData.piles)
    setCars(queueData.cars)
    setSessions(sessionData.sessions)
  }, [])

  useEffect(() => {
    refresh().catch((err) => setError(err instanceof Error ? err.message : '加载失败'))
    const timer = window.setInterval(() => refresh().catch(() => undefined), 5000)
    return () => window.clearInterval(timer)
  }, [refresh])

  async function triggerDispatch() {
    setError('')
    setMessage('')
    try {
      await api.dispatch()
      await refresh()
      setMessage('调度已完成：已按「最短完成时间」策略分配等候区车辆')
    } catch (err) {
      setError(err instanceof Error ? err.message : '调度失败')
    }
  }

  const engineRunning = overview?.engineStatus?.isRunning ?? true

  return (
    <div className="page-grid">
      <section className="card hero-card">
        <div>
          <p className="eyebrow">系统概览</p>
          <h2>充电站运行状态</h2>
          <p className="muted">
            管理员可启停充电桩、触发调度、监控充电区与等候区。故障默认采用优先级调度。
          </p>
        </div>
        <div className="button-row">
          <button type="button" className="btn btn-primary" onClick={triggerDispatch}>
            手动触发调度
          </button>
          <Link to="/admin/monitor" className="btn btn-secondary">充电区监控</Link>
        </div>
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
          <strong>{stats.totalQueuedCars ?? 0} / {SYSTEM_CONFIG.waitingCapacity}</strong>
        </div>
        <div className="metric-card">
          <span>累计收入</span>
          <strong>¥{(stats.totalRevenue ?? 0).toFixed(2)}</strong>
        </div>
        <div className="metric-card">
          <span>调度引擎</span>
          <strong>{engineRunning ? '运行中' : '已暂停'}</strong>
        </div>
        <div className="metric-card">
          <span>累计调度</span>
          <strong>{overview?.engineStatus?.totalDispatched ?? 0}</strong>
        </div>
      </section>

      <section className="card">
        <ChargingStationOverview
          piles={piles}
          cars={cars}
          sessions={sessions}
          compact
        />
      </section>

      <section className="card info-card">
        <h3>系统配置（验收参数）</h3>
        <div className="config-grid">
          <div><strong>快充桩</strong><span>A、B（{SYSTEM_CONFIG.fastPower} 度/小时）</span></div>
          <div><strong>慢充桩</strong><span>C、D、E（{SYSTEM_CONFIG.slowPower} 度/小时）</span></div>
          <div><strong>等候区容量 N</strong><span>{SYSTEM_CONFIG.waitingCapacity} 个车位</span></div>
          <div><strong>桩队列长度 M</strong><span>{SYSTEM_CONFIG.pileQueueCapacity}（1 充电 + 2 等待）</span></div>
          <div><strong>峰/平/谷电价</strong><span>{SYSTEM_CONFIG.peakPrice} / {SYSTEM_CONFIG.normalPrice} / {SYSTEM_CONFIG.valleyPrice} 元/度</span></div>
          <div><strong>服务费</strong><span>{SYSTEM_CONFIG.serviceFee} 元/度</span></div>
        </div>
      </section>

      <section className="card">
        <h3>快捷入口</h3>
        <div className="quick-links">
          <Link to="/admin/piles" className="quick-link">充电桩启停与故障模拟</Link>
          <Link to="/admin/monitor" className="quick-link">充电区 / 等候区监控</Link>
          <Link to="/admin/acceptance" className="quick-link">验收用例自动测试</Link>
          <Link to="/admin/reports" className="quick-link">日 / 周 / 月统计报表</Link>
        </div>
      </section>
    </div>
  )
}
