import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'
import type { ChargingPile } from '../../api/types'
import StatusBadge, { formatMode } from '../../components/StatusBadge'
import { PILE_ALIAS, PILE_LABELS, SYSTEM_CONFIG } from '../../utils/pileLabels'

function pileEnabled(pile: ChargingPile) {
  return pile.isEnabled ?? pile.isActive ?? pile.status !== 'FAULT'
}

export default function PilesPage() {
  const [piles, setPiles] = useState<ChargingPile[]>([])
  const [strategy, setStrategy] = useState<'priority' | 'time-sequence'>('priority')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loadingId, setLoadingId] = useState('')

  const refresh = useCallback(async () => {
    const result = await api.getAdminPiles()
    setPiles(result.piles)
  }, [])

  useEffect(() => {
    refresh().catch((err) => setError(err instanceof Error ? err.message : '加载失败'))
    const timer = window.setInterval(() => refresh().catch(() => undefined), 5000)
    return () => window.clearInterval(timer)
  }, [refresh])

  async function runPileAction(pileId: string, action: () => Promise<unknown>, successMessage: string) {
    setLoadingId(pileId)
    setError('')
    setMessage('')
    try {
      await action()
      await refresh()
      setMessage(successMessage)
    } catch (err) {
      setError(err instanceof Error ? err.message : '操作失败')
    } finally {
      setLoadingId('')
    }
  }

  function statusTone(status: string) {
    if (status === 'CHARGING') return 'success'
    if (status === 'FAULT' || status === 'OFFLINE') return 'danger'
    return 'default'
  }

  return (
    <div className="page-grid">
      <section className="card hero-card compact">
        <div>
          <p className="eyebrow">充电桩管理</p>
          <h2>启动 / 关闭 / 故障模拟</h2>
          <p className="muted">
            验收默认策略：优先级调度（暂停等候区叫号，优先迁移故障桩队列车辆）。
          </p>
        </div>
        <label className="inline-label">
          故障调度策略
          <select value={strategy} onChange={(e) => setStrategy(e.target.value as 'priority' | 'time-sequence')}>
            <option value="priority">优先级调度</option>
            <option value="time-sequence">时间顺序调度</option>
          </select>
        </label>
      </section>

      {message && <div className="alert alert-success">{message}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      <section className="pile-grid">
        {piles.map((pile) => {
          const enabled = pileEnabled(pile)
          const label = PILE_LABELS[pile.pileId] || pile.pileId
          const alias = PILE_ALIAS[pile.pileId]
          return (
            <article key={pile.pileId} className={`card pile-card ${enabled ? '' : 'pile-offline'}`}>
              <div className="pile-head">
                <div>
                  <h3>{label}</h3>
                  <p>{formatMode(pile.pileType)} · {pile.power} 度/小时 · 队列 {pile.queueCount ?? 0}/{SYSTEM_CONFIG.pileQueueCapacity}</p>
                </div>
                <StatusBadge value={pile.status} tone={statusTone(pile.status)} />
              </div>
              <dl className="pile-stats">
                <dt>验收别名</dt><dd>{alias}</dd>
                <dt>累计次数</dt><dd>{pile.totalSessions}</dd>
                <dt>累计时长</dt><dd>{pile.totalHours.toFixed(2)} h</dd>
                <dt>累计电量</dt><dd>{pile.totalEnergy.toFixed(2)} 度</dd>
              </dl>
              <div className="button-row">
                {enabled ? (
                  <>
                    <button
                      type="button"
                      className="btn btn-danger"
                      disabled={loadingId === pile.pileId}
                      onClick={() => runPileAction(
                        pile.pileId,
                        () => api.powerOffPile(pile.pileId, strategy),
                        `${label} 已关闭`,
                      )}
                    >
                      关闭
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      disabled={loadingId === pile.pileId}
                      onClick={() => runPileAction(
                        pile.pileId,
                        () => api.reportFault(pile.pileId, strategy),
                        `${label} 已模拟故障并重新调度`,
                      )}
                    >
                      模拟故障
                    </button>
                  </>
                ) : (
                  <button
                    type="button"
                    className="btn btn-primary"
                    disabled={loadingId === pile.pileId}
                    onClick={() => runPileAction(
                      pile.pileId,
                      () => api.recoverPile(pile.pileId),
                      `${label} 已恢复`,
                    )}
                  >
                    启动 / 恢复
                  </button>
                )}
              </div>
            </article>
          )
        })}
      </section>
    </div>
  )
}
