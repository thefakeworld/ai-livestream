"use client";

import { useState } from "react";

interface PlaybackControlsProps {
  isPlaying: boolean;
  loading: boolean;
  onStart: () => void;
  onStop: () => void;
  onNext: () => void;
  platforms: { enabled: boolean; has_stream_key: boolean }[];
}

export default function PlaybackControls({
  isPlaying,
  loading,
  onStart,
  onStop,
  onNext,
  platforms,
}: PlaybackControlsProps) {
  const [volume, setVolume] = useState(80);

  const enabledCount = platforms.filter(p => p.enabled && p.has_stream_key).length;

  return (
    <div className="flex flex-col h-full">
      {/* 标题 */}
      <div className="p-3 border-b border-white/5">
        <h3 className="font-semibold text-sm flex items-center gap-2">
          <span>🎛️</span> 播放控制
        </h3>
      </div>

      {/* 主控制按钮 */}
      <div className="p-3 space-y-2">
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={onStart}
            disabled={loading || isPlaying}
            className={`py-3 rounded-xl text-sm font-medium transition-all flex items-center justify-center gap-1 ${
              isPlaying
                ? "bg-gray-700 text-gray-500 cursor-not-allowed"
                : "bg-gradient-to-r from-emerald-500 to-green-600 text-white hover:opacity-90"
            }`}
          >
            <span>▶️</span>
            <span>开始</span>
          </button>
          <button
            onClick={onStop}
            disabled={loading || !isPlaying}
            className={`py-3 rounded-xl text-sm font-medium transition-all flex items-center justify-center gap-1 ${
              !isPlaying
                ? "bg-gray-700 text-gray-500 cursor-not-allowed"
                : "bg-gradient-to-r from-red-500 to-rose-600 text-white hover:opacity-90"
            }`}
          >
            <span>⏹️</span>
            <span>停止</span>
          </button>
        </div>

        <button
          onClick={onNext}
          disabled={loading || !isPlaying}
          className="w-full py-2 rounded-xl text-sm font-medium bg-gradient-to-r from-blue-500 to-cyan-600 text-white hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1"
        >
          <span>⏭️</span>
          <span>下一个</span>
        </button>
      </div>

      {/* 音量控制 */}
      <div className="p-3 border-t border-white/5">
        <div className="flex items-center gap-2">
          <span className="text-sm">🔊</span>
          <input
            type="range"
            min="0"
            max="100"
            value={volume}
            onChange={(e) => setVolume(parseInt(e.target.value))}
            className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
          />
          <span className="text-xs text-gray-400 w-8">{volume}%</span>
        </div>
      </div>

      {/* 推流状态 */}
      <div className="p-3 border-t border-white/5">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-400">推流平台</span>
          <span className={`text-xs font-medium ${enabledCount > 0 ? "text-emerald-400" : "text-gray-500"}`}>
            {enabledCount} 个已连接
          </span>
        </div>
        <div className="flex flex-wrap gap-1">
          {enabledCount > 0 ? (
            <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-1 rounded">
              ● 推流中
            </span>
          ) : (
            <span className="text-xs bg-gray-700 text-gray-400 px-2 py-1 rounded">
              本地预览模式
            </span>
          )}
        </div>
      </div>

      {/* 快捷设置 */}
      <div className="flex-1" />
      
      <div className="p-3 border-t border-white/5 space-y-1">
        <button className="w-full py-2 text-xs bg-gray-700/50 text-gray-400 rounded-lg hover:bg-gray-700 flex items-center justify-center gap-1">
          <span>⚙️</span> 高级设置
        </button>
        <button className="w-full py-2 text-xs bg-gray-700/50 text-gray-400 rounded-lg hover:bg-gray-700 flex items-center justify-center gap-1">
          <span>📊</span> 查看日志
        </button>
      </div>
    </div>
  );
}
