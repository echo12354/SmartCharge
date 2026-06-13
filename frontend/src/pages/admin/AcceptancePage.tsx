import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'
import type { AcceptanceEvent, StationSnapshot } from '../../api/types'
import ChargingStationBoard from '../../components/ChargingStationBoard'

export default function AcceptancePage() {
  const [events, setEvents] = useState<AcceptanceEvent[]>([])
  const [snapshot, setSnapshot] = useState<StationSnapshot | null>(null)
  const [lastResult, setLastResult] = useState<string>('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [stopAt, setStopAt] = useState('09:30')
  const [strategy, setStrategy] = useState<'priority' | 'time-sequence'>('priority')

  const refresh = useCallback(async () => {
    const [eventList, snap] = await Promise.all([
      api.listAcceptanceEvents(),
      api.getStationSnapshot(),
    ])
    setEvents(eventList.events)
    setSnapshot(snap)
  }, [])

  useEffect(() => {
    refresh().catch((err) => setError(err instanceof Error ? err.message : '加载失败'))
  }, [refresh])

  async function runAction(action: () => Promise<unknown>, successMessage: string) {
    setLoading(true)
    setError('')
    setMessage('')
    try {
      const result = await action()
      const data = result as { event?: string; simTime?: string; index?: number }
      if (data.event) {
        setLastResult(`#${data.index} ${data.simTime} ${data.event}`)
      }
      await refresh()
      setMessage(successMessage)
    } catch (err) {
      setError(err instanceof Error ? err.message : '执行失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-grid">
      <section className="card hero-card">
        <div>
          <p className="eyebrow">验收测试</p>
          <h2>《作业验收用例》自动执行</h2>
          <p className="muted">
            共 42 条事件，比例尺 1:10（6:00 起算）。执行后下方显示与 Excel 表一致的充电区 / 等候区填写格式。
          </p>
        </div>
      </section>

      {message && <div className="alert alert-success">{message}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      <section className="card">
        <h3>测试控制</h3>
        <div className="form inline-form">
          <label>
            截止模拟时刻
            <select value={stopAt} onChange={(e) => setStopAt(e.target.value)}>
              <option value="06:05">06:05（验证范例）</option>
              <option value="09:30">09:30（验收截止）</option>
              <option value="10:50">10:50（全部 42 条）</option>
            </select>
          </label>
          <label>
            故障策略
            <select value={strategy} onChange={(e) => setStrategy(e.target.value as 'priority' | 'time-sequence')}>
              <option value="priority">优先级调度</option>
              <option value="time-sequence">时间顺序调度</option>
            </select>
          </label>
        </div>
        <div className="button-row">
          <button type="button" className="btn btn-secondary" disabled={loading} onClick={() => runAction(() => api.resetAcceptance(), '验收环境已重置')}>
            重置环境
          </button>
          <button type="button" className="btn btn-secondary" disabled={loading} onClick={() => runAction(() => api.runAcceptanceNext(strategy), '已执行下一条事件')}>
            执行下一条
          </button>
          <button type="button" className="btn btn-primary" disabled={loading} onClick={() => runAction(() => api.runAcceptanceAll(stopAt, strategy), `已自动执行至 ${stopAt}`)}>
            一键执行到截止时刻
          </button>
        </div>
        {lastResult && <p className="muted">最近事件：{lastResult}</p>}
        {snapshot?.lastEventIndex != null && (
          <p className="muted">已执行：{snapshot.lastEventIndex} / {events.length} 条</p>
        )}
      </section>

      <section className="card">
        <ChargingStationBoard snapshot={snapshot} title="当前验收表填写快照" />
      </section>

      <section className="card table-card">
        <h3>事件清单（42 条）</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>序号</th>
                <th>模拟时刻</th>
                <th>事件</th>
                <th>说明</th>
              </tr>
            </thead>
            <tbody>
              {events.map((item) => (
                <tr key={item.index} className={snapshot?.lastEventIndex === item.index ? 'row-active' : ''}>
                  <td>{item.index}</td>
                  <td>{item.simTime}</td>
                  <td><code>{item.event}</code></td>
                  <td>{describeEvent(item.event)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

function describeEvent(event: string): string {
  if (event.startsWith('(A,')) {
    if (event.includes(',O,0)')) return '取消充电'
    const mode = event.includes(',F,') ? '快充' : '慢充'
    return `到达 · ${mode}`
  }
  if (event.startsWith('(B,')) {
    return event.endsWith(',O,0)') ? '桩故障/关闭' : '桩恢复'
  }
  if (event.startsWith('(C,')) return '修改充电量'
  return '-'
}
