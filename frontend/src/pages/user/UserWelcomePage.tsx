import { Link } from 'react-router-dom'

const featureCards = [
  {
    title: '预约充电',
    description: '选择快充或慢充，提前安排本次充电。',
    to: '/user/charge',
  },
  {
    title: '排队可见',
    description: '实时查看排队进度和车辆充电状态。',
    to: '/user/status',
  },
  {
    title: '账单查询',
    description: '自动完成计费，随时查询账单明细。',
    to: '/user/bills',
  },
]

export default function UserWelcomePage() {
  return (
    <div className="page-grid intro-home">
      <section className="card hero-card intro-hero">
        <div className="intro-copy">
          <p className="eyebrow">SmartCharge</p>
          <h2>智能充电，更省时、更省心</h2>
          <p className="muted">支持快充、慢充预约，实时查看排队进度与充电状态，自动完成计费与账单查询。</p>
          <div className="intro-summary">
            <span>预约充电</span>
            <span>排队查询</span>
            <span>自动计费</span>
            <span>账单管理</span>
          </div>
        </div>
        <div className="intro-visual hero-soft-visual" aria-hidden="true">
          <div className="soft-glow" />
          <div className="decorative-bolt" />
        </div>
      </section>

      <section className="intro-card-grid">
        {featureCards.map((item, index) => (
          <Link key={item.title} to={item.to} className="card intro-feature-card">
            <span className="intro-feature-mark">{String(index + 1).padStart(2, '0')}</span>
            <h3>{item.title}</h3>
            <p>{item.description}</p>
          </Link>
        ))}
      </section>
    </div>
  )
}
