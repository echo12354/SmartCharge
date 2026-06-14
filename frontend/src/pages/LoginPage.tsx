import { FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../contexts/AuthContext'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('user')
  const [password, setPassword] = useState('123')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      const user = await api.login(username, password)
      login(user)
      navigate(user.role === 'admin' ? '/admin' : '/user')
    } catch (err) {
      setError(err instanceof Error ? err.message : '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <section className="auth-showcase">
        <div className="auth-orbit" />
        <span className="brand-icon large">⚡</span>
        <p className="eyebrow">SmartCharge</p>
        <h2>智能充电，更省时、更省心</h2>
        <p>支持快充、慢充预约，实时查看排队进度与充电状态，自动完成计费与账单查询。</p>
      </section>
      <div className="auth-card refined-auth-card">
        <div className="auth-header">
          <span className="brand-icon large">⚡</span>
          <h1>SmartCharge</h1>
          <p>智能充电桩调度计费系统</p>
        </div>
        <form className="form" onSubmit={handleSubmit}>
          <label>
            用户名
            <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="user / admin" required />
          </label>
          <label>
            密码
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </label>
          {error && <div className="alert alert-error">{error}</div>}
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? '登录中...' : '登录'}
          </button>
        </form>
        <p className="auth-footer">
          还没有账号？<Link to="/register">立即注册</Link>
        </p>
        <div className="hint-box">
          <strong>测试账号</strong>
          <div className="hint-row"><span>用户端</span><strong>user / 123</strong></div>
          <div className="hint-row"><span>管理员</span><strong>admin / 123</strong></div>
        </div>
      </div>
    </div>
  )
}
