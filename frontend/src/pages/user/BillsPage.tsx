import { Fragment, useEffect, useState } from 'react'
import { api } from '../../api/client'
import type { Bill } from '../../api/types'
import StatusBadge, { formatDateTime, formatMoney } from '../../components/StatusBadge'
import { useAuth } from '../../contexts/AuthContext'

export default function BillsPage() {
  const { user } = useAuth()
  const [bills, setBills] = useState<Bill[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getUserBills(user!.username)
      .then((result) => setBills(result.bills))
      .catch((err) => setError(err instanceof Error ? err.message : '加载失败'))
      .finally(() => setLoading(false))
  }, [user])

  const totalCost = bills.reduce((sum, bill) => sum + bill.totalFee, 0)
  const totalEnergy = bills.reduce((sum, bill) => sum + bill.energyAmount, 0)

  return (
    <div className="page-grid">
      <section className="card hero-card compact">
        <div>
          <p className="eyebrow">我的充电详单</p>
          <h2>{bills.length} 条记录</h2>
        </div>
        <div className="stat-row">
          <div><span>累计电量</span><strong>{totalEnergy.toFixed(2)} 度</strong></div>
          <div><span>累计费用</span><strong>{formatMoney(totalCost)}</strong></div>
        </div>
      </section>

      {error && <div className="alert alert-error">{error}</div>}

      <section className="card table-card">
        {loading ? (
          <p className="muted">加载中...</p>
        ) : bills.length === 0 ? (
          <p className="muted">暂无充电详单，完成一次充电后将在此显示。</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>详单编号</th>
                  <th>生成时间</th>
                  <th>充电桩</th>
                  <th>充电电量</th>
                  <th>时长</th>
                  <th>启动时间</th>
                  <th>停止时间</th>
                  <th>电价类型</th>
                  <th>充电费</th>
                  <th>服务费</th>
                  <th>总费用</th>
                </tr>
              </thead>
              <tbody>
                {bills.map((bill) => (
                  <Fragment key={bill.billId}>
                    <tr>
                      <td>{bill.billId}</td>
                      <td>{formatDateTime(bill.createdAt)}</td>
                      <td>{bill.pileId}</td>
                      <td>{bill.energyAmount} 度</td>
                      <td>{bill.durationHours.toFixed(2)} h</td>
                      <td>{formatDateTime(bill.startTime)}</td>
                      <td>{formatDateTime(bill.endTime)}</td>
                      <td><StatusBadge value={bill.priceType} tone="info" /></td>
                      <td>{formatMoney(bill.chargeFee)}</td>
                      <td>{formatMoney(bill.serviceFee)}</td>
                      <td><strong>{formatMoney(bill.totalFee)}</strong></td>
                    </tr>
                    {(bill.priceBreakdown?.length ?? 0) > 1 && (
                      <tr>
                        <td colSpan={11}>
                          <div className="muted">
                            分时计费明细：
                            {bill.priceBreakdown!.map((item, index) => (
                              <span key={`${bill.billId}-${index}`}>
                                {index > 0 ? '；' : ''}
                                <StatusBadge value={item.priceType} tone="info" />
                                {item.energyAmount.toFixed(2)} 度 x {formatMoney(item.unitPrice)} = {formatMoney(item.fee)}
                              </span>
                            ))}
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
