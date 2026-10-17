import React from 'react'

export const DashboardSkeleton: React.FC = () => {
  return (
    <div className="h-full overflow-y-auto p-6 bg-[#090D18] space-y-6 animate-pulse">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header Skeleton */}
        <div className="flex items-center justify-between pb-4 border-b border-[#202B3F]">
          <div className="space-y-2">
            <div className="h-6 w-48 bg-[#151C2B] rounded-lg" />
            <div className="h-3 w-64 bg-[#121824] rounded" />
          </div>
          <div className="h-8 w-28 bg-[#151C2B] rounded-lg" />
        </div>

        {/* 4 Cards Skeleton */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 bg-[#121824] border border-[#202B3F] rounded-xl p-4 space-y-3">
              <div className="h-3 w-20 bg-[#151C2B] rounded" />
              <div className="h-8 w-16 bg-[#151C2B] rounded" />
              <div className="h-2 w-full bg-[#101623] rounded-full" />
            </div>
          ))}
        </div>

        {/* Middle Columns Skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-7 h-72 bg-[#121824] border border-[#202B3F] rounded-xl p-6 space-y-4">
            <div className="h-4 w-36 bg-[#151C2B] rounded" />
            <div className="h-24 bg-[#151C2B] rounded-lg" />
            <div className="h-24 bg-[#151C2B] rounded-lg" />
          </div>
          <div className="lg:col-span-5 h-72 bg-[#121824] border border-[#202B3F] rounded-xl p-6 space-y-4">
            <div className="h-4 w-40 bg-[#151C2B] rounded" />
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-14 bg-[#151C2B] rounded-lg" />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export const TaskBoardSkeleton: React.FC = () => {
  return (
    <div className="h-full flex flex-col bg-[#090D18] overflow-hidden animate-pulse">
      <div className="h-14 px-6 border-b border-[#202B3F] flex items-center justify-between bg-[#121824]">
        <div className="h-6 w-44 bg-[#151C2B] rounded-lg" />
        <div className="flex gap-3">
          <div className="h-8 w-28 bg-[#151C2B] rounded-lg" />
          <div className="h-8 w-24 bg-[#151C2B] rounded-lg" />
        </div>
      </div>

      <div className="flex-1 p-6 grid grid-cols-1 md:grid-cols-4 gap-5">
        {[1, 2, 3, 4].map((col) => (
          <div key={col} className="bg-[#121824] border border-[#202B3F] rounded-xl flex flex-col p-3 space-y-3">
            <div className="h-6 w-24 bg-[#151C2B] rounded" />
            <div className="h-32 bg-[#151C2B] rounded-lg" />
            <div className="h-32 bg-[#151C2B] rounded-lg" />
          </div>
        ))}
      </div>
    </div>
  )
}

export const ChatSkeleton: React.FC = () => {
  return (
    <div className="h-full flex flex-col bg-[#090D18] animate-pulse">
      <div className="h-12 px-6 border-b border-[#202B3F] flex items-center bg-[#121824]">
        <div className="h-5 w-32 bg-[#151C2B] rounded" />
      </div>
      <div className="flex-1 p-6 space-y-5">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex gap-4 items-start">
            <div className="w-10 h-10 rounded-full bg-[#151C2B] shrink-0" />
            <div className="space-y-2 flex-1">
              <div className="h-3 w-36 bg-[#151C2B] rounded" />
              <div className="h-4 w-3/4 bg-[#121824] rounded" />
            </div>
          </div>
        ))}
      </div>
      <div className="p-4 bg-[#121824] border-t border-[#202B3F]">
        <div className="h-12 bg-[#151C2B] rounded-xl border border-[#202B3F]" />
      </div>
    </div>
  )
}
