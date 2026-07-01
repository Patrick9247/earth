// 格式化日期为 yyyy-MM-dd HH:mm:ss
export const formatDate = (dateStr: string | null | undefined | Date): string => {
  if (!dateStr) return '-'
  const date = dateStr instanceof Date ? dateStr : new Date(dateStr)
  if (Number.isNaN(date.getTime())) return '-'

  const parts = [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, '0'),
    String(date.getDate()).padStart(2, '0')
  ]

  const time = [
    String(date.getHours()).padStart(2, '0'),
    String(date.getMinutes()).padStart(2, '0'),
    String(date.getSeconds()).padStart(2, '0')
  ]

  return `${parts.join('-')} ${time.join(':')}`
}
