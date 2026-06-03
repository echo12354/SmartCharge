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
      <div className="auth-card">
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
          <span>用户：user / 123</span>
          <span>管理员：admin / 123</span>
        </div>
      </div>
    </div>
  )
}
