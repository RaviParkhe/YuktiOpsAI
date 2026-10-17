import React from 'react'
import YuktiCoreScene from './YuktiCoreScene'

interface YuktiCore3DProps {
  className?: string
  scrollProgress?: number
  onNodeClick?: (nodeKey: string) => void
}

export const YuktiCore3D: React.FC<YuktiCore3DProps> = ({
  className = '',
  scrollProgress = 0,
}) => {
  return (
    <div className={`relative w-full h-full flex items-center justify-center ${className}`}>
      <YuktiCoreScene scrollProgress={scrollProgress} />
    </div>
  )
}

export default YuktiCore3D
