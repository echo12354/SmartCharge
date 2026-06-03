import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import type { ReportRow } from '../../api/types'
import { formatMoney } from '../../components/StatusBadge'

const RANGES = [
  { value: 'day', label: '今日' },
  { value: 'week', label: '本周' },
  { value: 'month', label: '本月' },
  { value: 'all', label: '全部' },
]

export default function ReportsPage() {
  const [timeRange, setTimeRange] = useState('all')
  const [reports, setReports] = useState<ReportRow[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.getReports(timeRange)
      .then((result) => setReports(result.reports))
      .catch((err) => setError(err instanceof Error ? err.message : '加载失败'))
      .finally(() => setLoading(false))
  }, [timeRange])

  const totals = reports.reduce(
    (acc, row) => ({
      chargeCount: acc.chargeCount + row.chargeCount,
      chargeDuration: acc.chargeDuration + row.chargeDuration,
      energyAmount: acc.energyAmount + row.energyAmount,
      chargeFee: acc.chargeFee + row.chargeFee,
      serviceFee: acc.serviceFee + row.serviceFee,
      totalFee: acc.totalFee + row.totalFee,
    }),
    { chargeCount: 0, chargeDuration: 0, energyAmount: 0, chargeFee: 0, serviceFee: 0, totalFee: 0 },
  )

  return (
    <div className="page-grid">
      <section className="card hero-card compact">
        <div>
          <p className="eyebrow">统计报表</p>
          <h2>充电桩运营数据</h2>
        </div>
        <div className="tab-row">
          {RANGES.map((range) => (
            <button
              key={range.value}
              type="button"
              className={`tab-btn ${timeRange === range.value ? 'active' : ''}`}
              onClick={() => setTimeRange(range.value)}
            >
              {range.label}
            </button>
          ))}
        </div>
      </section>

      <section className="metrics-grid">
        <div className="metric-card"><span>累计次数</span><strong>{totals.chargeCount}</strong></div>
        <div className="metric-card"><span>累计时长</span><strong>{totals.chargeDuration.toFixed(2)} h</strong></div>
        <div className="metric-card"><span>累计电量</span><strong>{totals.energyAmount.toFixed(2)} 度</strong></div>
        <div className="metric-card"><span>累计总费用</span><strong>{formatMoney(totals.totalFee)}</strong></div>
      </section>

      {error && <div className="alert alert-error">{error}</div>}

      <section className="card table-card">
        {loading ? (
          <p className="muted">加载中...</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>充电桩</th>
                  <th>时间范围</th>
                  <th>累计次数</th>
                  <th>累计时长 (h)</th>
                  <th>累计电量 (度)</th>
                  <th>累计充电费</th>
                  <th>累计服务费</th>
                  <th>累计总费用</th>
                </tr>
              </thead>
              <tbody>
                {reports.map((row) => (
                  <tr key={row.pileId}>
                    <td>{row.pileName}</td>
                    <td>{RANGES.find((item) => item.value === row.timeRange)?.label || row.timeRange}</td>
                    <td>{row.chargeCount}</td>
                    <td>{row.chargeDuration.toFixed(2)}</td>
                    <td>{row.energyAmount.toFixed(2)}</td>
                    <td>{formatMoney(row.chargeFee)}</td>
                    <td>{formatMoney(row.serviceFee)}</td>
                    <td><strong>{formatMoney(row.totalFee)}</strong></td>
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
