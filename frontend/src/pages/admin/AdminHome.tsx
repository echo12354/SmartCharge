import { Link } from 'react-router-dom'

const adminEntries = [
  {
    title: '充电区监控',
    description: '查看车辆充电进度与桩内队列。',
    to: '/admin/monitor',
  },
  {
    title: '充电桩管理',
    description: '处理启停、故障上报和恢复。',
    to: '/admin/piles',
  },
  {
    title: '等候队列',
    description: '查看等候区与充电桩队列。',
    to: '/admin/queue',
  },
  {
    title: '验收测试',
    description: '按事件流演示系统调度过程。',
    to: '/admin/acceptance',
  },
  {
    title: '统计报表',
    description: '查看运营数据与费用统计。',
    to: '/admin/reports',
  },
]

export default function AdminHome() {
  return (
    <div className="page-grid intro-home">
      <section className="card hero-card intro-hero">
        <div className="intro-copy">
          <p className="eyebrow">管理后台</p>
          <h2>SmartCharge 充电调度计费系统后台</h2>
          <p className="muted">面向充电站运营的监控、队列、故障处理、验收测试与统计报表入口。</p>
          <div className="intro-summary">
            <span>后台监控</span>
            <span>桩位管理</span>
            <span>队列调度</span>
            <span>统计报表</span>
          </div>
        </div>
        <div className="admin-hero-panel" aria-hidden="true">
          <div>
            <strong>2</strong>
            <span>快充桩</span>
          </div>
          <div>
            <strong>3</strong>
            <span>慢充桩</span>
          </div>
          <div>
            <strong>10</strong>
            <span>等候区容量</span>
          </div>
        </div>
      </section>

      <section className="admin-entry-grid">
        {adminEntries.map((item, index) => (
          <Link key={item.to} to={item.to} className="card admin-entry-card">
            <span className="intro-feature-mark">{String(index + 1).padStart(2, '0')}</span>
            <div>
              <h3>{item.title}</h3>
              <p>{item.description}</p>
            </div>
          </Link>
        ))}
      </section>
    </div>
  )
}
