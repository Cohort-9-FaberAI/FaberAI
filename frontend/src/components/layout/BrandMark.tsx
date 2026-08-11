import { useStore } from '../../store'

export default function BrandMark({
  size = 30,
  variant = 'default',
  className = '',
}: {
  size?: number
  variant?: 'default' | 'white' | 'full' | 'full-white'
  className?: string
}) {
  const theme = useStore((s) => s.theme)
  const isDark = theme === 'dark'

  const src =
    variant === 'white'
      ? '/logo-white.svg'
      : variant === 'full-white'
        ? '/logo-full-white.svg'
        : variant === 'full'
          ? isDark
            ? '/logo-full-white.svg'
            : '/logo-full.svg'
          : isDark
            ? '/logo-white.svg'
            : '/logo.svg'

  const width = variant === 'full' || variant === 'full-white' ? Math.round(size * 1.78) : size

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
