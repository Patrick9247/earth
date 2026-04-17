// 格式化日期为 yyyy-MM-dd
export const formatDate = (dateStr: string | null | undefined | Date): string => {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) return '-'
    console.log('Parsed date:', date)
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hour = String(date.getHours()).padStart(2, '0')
    const minute = String(date.getMinutes()).padStart(2, '0')
    const second = String(date.getSeconds()).padStart(2, '0')
    return `${year}-${month}-${day}-${hour}:${minute}:${second}`
  } catch {
    return '-'
  }
}