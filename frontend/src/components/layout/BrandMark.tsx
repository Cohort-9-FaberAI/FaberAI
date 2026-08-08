export default function BrandMark({
  size = 30,
  variant = 'default',
  className = '',
}: {
  size?: number
  variant?: 'default' | 'white' | 'full'
  className?: string
}) {
  const src =
    variant === 'white' ? '/logo-white.svg' : variant === 'full' ? '/logo-full.svg' : '/logo.svg'

  const width = variant === 'full' ? Math.round(size * 1.78) : size

  return (
    <img
      src={src}
      alt="Faber AI"
      width={width}
      height={size}
      className={`brand-mark brand-mark-${variant} ${className}`.trim()}
      style={{
        height: `${size}px`,
        width: variant === 'full' ? 'auto' : `${size}px`,
        objectFit: 'contain',
        display: 'inline-block',
        verticalAlign: 'middle',
      }}
    />
  )
}
