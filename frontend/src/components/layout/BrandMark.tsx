export default function BrandMark({ size = 30 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
      <path d="M6 26V10L16 4L26 10V26L20 22V13.5L16 11L12 13.5V22L6 26Z" fill="var(--ferrule)" />
      <path d="M16 11L20 13.5V22L16 19.5V11Z" fill="var(--toolpath)" opacity="0.85" />
    </svg>
  )
}
