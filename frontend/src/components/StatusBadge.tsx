const LABELS: Record<string, string> = {
  WAITING: '等候区',
  WAITING_AREA: '等候区',
  DISPATCHED: '已调度',
  PILE_QUEUE: '桩队列',
  CHARGING: '充电中',
  COMPLETED: '已完成',
  CANCELLED: '已取消',
  ACTIVE: '空闲',
  OFFLINE: '已关闭',
  FAULT: '故障',
  IDLE: '空闲',
  fast: '快充',
  slow: '慢充',
  PEAK: '峰时',
  NORMAL: '平时',
  VALLEY: '谷时',
  MIXED: '分时计费',
}

interface StatusBadgeProps {
  value: string
  tone?: 'default' | 'success' | 'warning' | 'danger' | 'info'
}

export default function StatusBadge({ value, tone = 'default' }: StatusBadgeProps) {
  const label = LABELS[value] || value
  return <span className={`badge badge-${tone}`}>{label}</span>
}

export function formatDateTime(value?: string | null) {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN')
}

export function formatMode(mode?: string) {
  if (!mode) return '-'
  return LABELS[mode] || mode
}

export function formatMoney(value?: number) {
  if (value == null) return '-'
  return `¥${value.toFixed(2)}`
}
