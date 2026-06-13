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
          <p className="muted">面向管理员的充电站运营、调度与计费管理入口。</p>
        </div>
        <div className="hero-tags intro-tags">
          <span>调度</span>
          <span>故障</span>
          <span>计费</span>
        </div>
      </section>

      <section className="admin-entry-grid">
        {adminEntries.map((item) => (
          <Link key={item.to} to={item.to} className="card admin-entry-card">
            <span className="intro-feature-mark">{item.title.slice(0, 1)}</span>
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
