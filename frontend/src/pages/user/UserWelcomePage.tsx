import { Link } from 'react-router-dom'

const featureCards = [
  {
    title: '提交充电请求',
    description: '选择快充或慢充，提交本次所需电量。',
  },
  {
    title: '查看排队状态',
    description: '查看排队号、前车数量和充电进度。',
  },
  {
    title: '查看充电详单',
    description: '查询账单、费用组成和历史充电记录。',
  },
]

export default function UserWelcomePage() {
  return (
    <div className="page-grid intro-home">
      <section className="card hero-card intro-hero">
        <div className="intro-copy">
          <p className="eyebrow">用户首页</p>
          <h2>欢迎使用 SmartCharge</h2>
          <p className="muted">智能充电调度与计费服务</p>
          <div className="intro-actions">
            <Link to="/user/charge" className="btn btn-primary">进入充电服务</Link>
            <Link to="/user/bills" className="btn btn-secondary">查看充电详单</Link>
          </div>
        </div>
        <div className="hero-tags intro-tags">
          <span>预约充电</span>
          <span>查看排队</span>
          <span>结束充电</span>
          <span>查看详单</span>
        </div>
      </section>

      <section className="intro-card-grid">
        {featureCards.map((item) => (
          <article key={item.title} className="card intro-feature-card">
            <span className="intro-feature-mark">{item.title.slice(0, 1)}</span>
            <h3>{item.title}</h3>
            <p>{item.description}</p>
          </article>
        ))}
      </section>
    </div>
  )
}
