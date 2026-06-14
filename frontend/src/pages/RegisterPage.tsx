import { FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../contexts/AuthContext'

export default function RegisterPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (password !== confirm) {
      setError('两次输入的密码不一致')
      return
    }
    setError('')
    setLoading(true)
    try {
      const user = await api.register(username, password)
      login(user)
      navigate('/user')
    } catch (err) {
      setError(err instanceof Error ? err.message : '注册失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <section className="auth-showcase">
        <div className="auth-orbit" />
        <span className="brand-icon large">⚡</span>
        <p className="eyebrow">新用户接入</p>
        <h2>创建账号后即可提交充电请求</h2>
        <p>注册后进入用户端，选择快充或慢充，系统自动生成排队号并跟踪充电状态。</p>
        <div className="auth-badges">
          <span>排队号 F/T</span>
          <span>状态追踪</span>
          <span>账单详单</span>
        </div>
      </section>
      <div className="auth-card refined-auth-card">
        <div className="auth-header">
          <span className="brand-icon large">⚡</span>
          <h1>用户注册</h1>
          <p>创建账号后即可提交充电请求</p>
        </div>
        <form className="form" onSubmit={handleSubmit}>
          <label>
            用户名
            <input value={username} onChange={(e) => setUsername(e.target.value)} required />
          </label>
          <label>
            密码
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </label>
          <label>
            确认密码
            <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required />
          </label>
          {error && <div className="alert alert-error">{error}</div>}
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? '注册中...' : '注册并登录'}
          </button>
        </form>
        <p className="auth-footer">
          已有账号？<Link to="/login">返回登录</Link>
        </p>
      </div>
    </div>
  )
}
