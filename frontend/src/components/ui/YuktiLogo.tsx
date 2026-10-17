import React from 'react'

export interface YuktiMarkProps {
  size?: number | string
  className?: string
  variant?: 'cyan' | 'monochrome'
}

/**
 * YuktiOps Connected Intelligence Mark
 * Represents engineering signals (Conversations, Code/Git, Execution)
 * converging into connected context and coordinated action.
 */
export const YuktiMark: React.FC<YuktiMarkProps> = ({
  size = 24,
  className = '',
  variant = 'cyan',
}) => {
  const isCyan = variant === 'cyan'
  const strokeColor = isCyan ? '#62CBE8' : 'currentColor'
  const nodeFill = isCyan ? '#62CBE8' : 'currentColor'
  const frameStroke = isCyan ? '#263246' : 'currentColor'

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`shrink-0 ${className}`}
      aria-label="YuktiOps Connected Intelligence Mark"
    >
      {/* Precision Geometric Coordinate Hexagon Frame */}
      <path
        d="M6.5 10.5L16 5L25.5 10.5V21.5L16 27L6.5 21.5Z"
        stroke={frameStroke}
        strokeWidth="1.5"
        strokeLinejoin="round"
        strokeOpacity={isCyan ? 0.7 : 0.35}
      />
      {/* Convergent Vector Flow Channels */}
      <path
        d="M6.5 10.5L16 16M25.5 10.5L16 16M16 16V27"
        stroke={strokeColor}
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Central Axis Synchronization Line */}
      <path
        d="M16 5V16"
        stroke={strokeColor}
        strokeWidth="1.25"
        strokeDasharray="2 2"
        strokeOpacity={0.6}
      />
      {/* Signal Ingestion Nodes */}
      <circle cx="6.5" cy="10.5" r="2.25" fill={nodeFill} />
      <circle cx="25.5" cy="10.5" r="2.25" fill={nodeFill} />
      <circle cx="16" cy="27" r="2.25" fill={nodeFill} />
      {/* Coordinated Intelligence Focal Hub */}
      <circle
        cx="16"
        cy="16"
        r="3.25"
        fill="#090D16"
        stroke={strokeColor}
        strokeWidth="1.8"
      />
      <circle cx="16" cy="16" r="1.3" fill={nodeFill} />
    </svg>
  )
}

export interface YuktiWordmarkProps {
  className?: string
  size?: 'xs' | 'sm' | 'base' | 'lg' | 'xl' | '2xl' | 'hero' | 'custom'
  textClassName?: string
  weight?: 'semibold' | 'bold'
}

/**
 * Hybrid-script YuktiOps Wordmark: "युक्तिOps"
 * "युक्ति" set in Marathi / Devanagari script (Noto Sans Devanagari)
 * "Ops" set in English Latin script (Geist Sans)
 * Matched visual baseline, balanced perceived weight, transparent background.
 */
export const YuktiWordmark: React.FC<YuktiWordmarkProps> = ({
  className = '',
  size = 'base',
  textClassName = '',
  weight = 'bold',
}) => {
  const sizeMap: Record<string, string> = {
    xs: 'text-xs',
    sm: 'text-sm',
    base: 'text-base',
    lg: 'text-lg',
    xl: 'text-xl',
    '2xl': 'text-2xl',
    hero: 'text-4xl sm:text-6xl md:text-7xl',
    custom: '',
  }

  const baseSize = sizeMap[size] || sizeMap.base
  const weightClass = weight === 'bold' ? 'font-bold' : 'font-semibold'

  return (
    <span
      className={`inline-flex items-baseline select-none ${baseSize} ${className}`}
      aria-label="युक्तिOps"
      role="img"
    >
      <span
        style={{ fontFamily: "var(--font-devanagari, 'Noto Sans Devanagari'), -apple-system, BlinkMacSystemFont, sans-serif" }}
        className={`${weightClass} text-[#F1F5F9] tracking-normal leading-none ${textClassName}`}
      >
        युक्ति
      </span>
      <span
        style={{ fontFamily: "var(--font-sans, 'Geist Sans'), -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" }}
        className={`${weightClass} text-[#62CBE8] tracking-tight leading-none ${textClassName}`}
      >
        Ops
      </span>
    </span>
  )
}

export interface YuktiLogoProps extends YuktiMarkProps {
  showWordmark?: boolean
  wordmarkSize?: 'xs' | 'sm' | 'base' | 'lg' | 'xl' | '2xl' | 'hero' | 'custom'
  wordmarkClassName?: string
  badgeText?: string
  badgeClassName?: string
  markContainerClassName?: string
  onClick?: () => void
}

export const YuktiLogo: React.FC<YuktiLogoProps> = ({
  size = 24,
  className = '',
  variant = 'cyan',
  showWordmark = true,
  wordmarkSize = 'base',
  wordmarkClassName = '',
  badgeText,
  badgeClassName = '',
  markContainerClassName = '',
  onClick,
}) => {
  return (
    <div
      onClick={onClick}
      className={`inline-flex items-center gap-2.5 ${onClick ? 'cursor-pointer' : ''} ${className}`}
    >
      <div className={`flex items-center justify-center shrink-0 ${markContainerClassName}`}>
        <YuktiMark size={size} variant={variant} />
      </div>
      {showWordmark && (
        <div className="flex items-center gap-2">
          <YuktiWordmark size={wordmarkSize} className={wordmarkClassName} />
          {badgeText && (
            <span
              className={`text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#111925] text-[#62CBE8] border border-[#263246] font-semibold select-none ${badgeClassName}`}
            >
              {badgeText}
            </span>
          )}
        </div>
      )}
    </div>
  )
}

export default YuktiLogo
