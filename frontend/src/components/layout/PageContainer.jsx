export default function PageContainer({ children, gap = 22 }) {
  return (
    <div style={{ padding: '30px 34px', display: 'flex', flexDirection: 'column', gap, maxWidth: 1180, width: '100%' }}>
      {children}
    </div>
  )
}
