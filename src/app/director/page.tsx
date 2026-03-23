"use client";

import { useEffect, useState, useCallback } from "react";

interface ContentItem {
  type: string;
  name: string;
  path: string;
  duration: number;
  artist: string;
  title: string;
  is_playing: boolean;
  started_at: string | null;
  position: number;
}

interface Platform {
  name: string;
  rtmp_url: string;
  stream_key: string;
  enabled: boolean;
  status: string;
  bitrate: string;
  fps: number;
}

interface DirectorStatus {
  success: boolean;
  is_streaming: boolean;
  ffmpeg_pid: number | null;
  uptime: number;
  mode: string;
  current_content: ContentItem | null;
  content_count: number;
  news_count: number;
  music_count: number;
  networkStatus: string;
  ffmpegProgress: {
    fps: number;
    bitrate: string;
    time: string;
  };
  contentProgress: number;
  remainingTime: number;
  timestamp: string;
  platforms?: Platform[];
  platform_config?: {
    enabled_count: number;
  };
}

export default function DirectorDashboard() {
  const [status, setStatus] = useState<DirectorStatus | null>(null);
  const [contentList, setContentList] = useState<ContentItem[]>([]);
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [activeTab, setActiveTab] = useState<"nowplaying" | "platforms" | "content">("nowplaying");

  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch("/api/director");
      const data = await response.json();
      setStatus(data);
    } catch (error) {
      console.error("Fetch status error:", error);
    }
  }, []);

  const fetchContentList = useCallback(async () => {
    try {
      const response = await fetch("/api/director?action=list");
      const data = await response.json();
      if (data.success && data.data) {
        setContentList(data.data);
      }
    } catch (error) {
      console.error("Fetch content list error:", error);
    }
  }, []);

  const fetchPlatforms = useCallback(async () => {
    try {
      const response = await fetch("/api/director?action=platforms");
      const data = await response.json();
      if (data.success && data.data) {
        setPlatforms(data.data);
      }
    } catch (error) {
      console.error("Fetch platforms error:", error);
    }
  }, []);

  const sendCommand = async (action: string, data?: any) => {
    setLoading(true);
    try {
      const response = await fetch("/api/director", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, data }),
      });
      const result = await response.json();
      console.log("Command result:", result);
      fetchStatus();
      fetchPlatforms();
      return result;
    } catch (error) {
      console.error("Command error:", error);
      return { success: false, error: String(error) };
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    fetchContentList();
    fetchPlatforms();
  }, [fetchStatus, fetchContentList, fetchPlatforms]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchStatus]);

  const formatTime = (seconds: number): string => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return h > 0 ? `${h}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}` : `${m}:${s.toString().padStart(2, "0")}`;
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "news": return "📰";
      case "music": return "🎵";
      case "video": return "🎬";
      default: return "📄";
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case "news": return "from-blue-500 to-cyan-500";
      case "music": return "from-purple-500 to-pink-500";
      case "video": return "from-orange-500 to-red-500";
      default: return "from-gray-500 to-gray-600";
    }
  };

  const getNetworkStatusDisplay = (ns: string) => {
    switch (ns) {
      case "connected": return { text: "已连接", color: "text-emerald-400", icon: "✅" };
      case "connecting": return { text: "连接中", color: "text-yellow-400", icon: "⏳" };
      case "closing": return { text: "断开中", color: "text-orange-400", icon: "⚠️" };
      case "disconnected": return { text: "已断开", color: "text-red-400", icon: "❌" };
      default: return { text: "检查中", color: "text-gray-400", icon: "❓" };
    }
  };

  const getPlatformIcon = (name: string) => {
    const icons: Record<string, string> = {
      "YouTube": "▶️",
      "TikTok": "🎵",
      "B站 (Bilibili)": "📺",
      "抖音": "🎵",
      "Twitch": "🎮",
      "Facebook": "👤",
      "快手": "⚡",
      "虎牙": "🐯",
      "斗鱼": "🐟",
      "小红书": "📕"
    };
    return icons[name] || "📡";
  };

  const networkDisplay = status ? getNetworkStatusDisplay(status.networkStatus) : null;
  const enabledPlatforms = platforms.filter(p => p.enabled && p.stream_key);

  return (
    <div className="min-h-screen bg-[#0a0e17] text-white">
      {/* Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-br from-[#0a0e17] via-[#0f1624] to-[#0a0e17]" />
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 min-h-screen flex flex-col">
        {/* Header */}
        <header className="px-6 py-4 border-b border-white/5 backdrop-blur-xl bg-black/20">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${status?.is_streaming ? 'bg-gradient-to-br from-emerald-500 to-green-600' : 'bg-gradient-to-br from-gray-600 to-gray-700'}`}>
                <span className="text-2xl">🎬</span>
              </div>
              <div>
                <h1 className="text-xl font-bold">智能导播台</h1>
                <p className="text-sm text-gray-400">多平台直播控制中心</p>
              </div>
              <div className={`ml-4 px-4 py-2 rounded-full text-sm font-medium ${status?.is_streaming ? 'bg-emerald-500/20 text-emerald-400' : 'bg-gray-700 text-gray-400'}`}>
                {status?.is_streaming ? `🔴 推流中 → ${enabledPlatforms.length}个平台` : '⏸️ 待机中'}
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-xs text-gray-500">更新时间</p>
                <p className="text-sm font-mono">{status?.timestamp || "--:--:--"}</p>
              </div>
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`px-4 py-2 rounded-lg text-sm transition-all ${autoRefresh ? 'bg-emerald-500/20 text-emerald-400' : 'bg-gray-700 text-gray-400'}`}
              >
                {autoRefresh ? '🔄 自动' : '⏸️ 暂停'}
              </button>
            </div>
          </div>
        </header>

        {/* Tab Navigation */}
        <div className="px-6 py-3 border-b border-white/5 bg-black/10">
          <div className="max-w-7xl mx-auto flex gap-2">
            {[
              { id: "nowplaying", label: "📺 正在播放" },
              { id: "platforms", label: "🌐 平台管理" },
              { id: "content", label: "📋 内容库" },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-4 py-2 rounded-lg text-sm transition-all ${activeTab === tab.id ? 'bg-emerald-500/20 text-emerald-400' : 'text-gray-400 hover:bg-white/5'}`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Main Content */}
        <main className="flex-1 p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            
            {/* Status Bar */}
            <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
              <div className="bg-gray-800/50 rounded-xl p-4 border border-white/5">
                <p className="text-xs text-gray-500 mb-1">网络状态</p>
                <p className={`font-semibold ${networkDisplay?.color}`}>
                  {networkDisplay?.icon} {networkDisplay?.text}
                </p>
              </div>
              <div className="bg-gray-800/50 rounded-xl p-4 border border-white/5">
                <p className="text-xs text-gray-500 mb-1">编码帧率</p>
                <p className="font-semibold">{status?.ffmpegProgress?.fps || 30} FPS</p>
              </div>
              <div className="bg-gray-800/50 rounded-xl p-4 border border-white/5">
                <p className="text-xs text-gray-500 mb-1">码率</p>
                <p className="font-semibold">{status?.ffmpegProgress?.bitrate || "2500 kbps"}</p>
              </div>
              <div className="bg-gray-800/50 rounded-xl p-4 border border-white/5">
                <p className="text-xs text-gray-500 mb-1">运行时长</p>
                <p className="font-semibold">{formatTime(status?.uptime || 0)}</p>
              </div>
              <div className="bg-gray-800/50 rounded-xl p-4 border border-white/5">
                <p className="text-xs text-gray-500 mb-1">推流平台</p>
                <p className="font-semibold text-emerald-400">{enabledPlatforms.length} 个</p>
              </div>
              <div className="bg-gray-800/50 rounded-xl p-4 border border-white/5">
                <p className="text-xs text-gray-500 mb-1">内容数量</p>
                <p className="font-semibold">{status?.content_count || 0} 项</p>
              </div>
            </div>

            {/* Now Playing Tab */}
            {activeTab === "nowplaying" && (
              <div className="space-y-6">
                <div className="bg-gray-800/50 rounded-2xl border border-white/5 overflow-hidden">
                  <div className="p-6 border-b border-white/5">
                    <h2 className="text-lg font-semibold flex items-center gap-2">
                      <span className="text-2xl">📺</span> 当前播放
                    </h2>
                  </div>
                  
                  <div className="p-6">
                    {status?.current_content ? (
                      <div className="space-y-4">
                        <div className="flex items-start gap-4">
                          <div className={`w-20 h-20 rounded-xl bg-gradient-to-br ${getTypeColor(status.current_content.type)} flex items-center justify-center text-3xl`}>
                            {getTypeIcon(status.current_content.type)}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="px-2 py-0.5 rounded text-xs bg-white/10">
                                {status.current_content.type === "news" ? "新闻播报" : status.current_content.type === "music" ? "音乐" : "视频"}
                              </span>
                              {status.is_streaming && (
                                <span className="flex items-center gap-1 text-emerald-400 text-xs">
                                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                                  正在播放
                                </span>
                              )}
                            </div>
                            <h3 className="text-xl font-bold mb-1">
                              {status.current_content.title || status.current_content.name}
                            </h3>
                            {status.current_content.artist && (
                              <p className="text-gray-400">艺术家: {status.current_content.artist}</p>
                            )}
                          </div>
                        </div>

                        <div className="space-y-2">
                          <div className="flex justify-between text-sm text-gray-400">
                            <span>{formatTime(status.current_content.position || 0)}</span>
                            <span>-{formatTime(status.remainingTime || 0)}</span>
                            <span>{formatTime(status.current_content.duration || 0)}</span>
                          </div>
                          <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                            <div 
                              className={`h-full bg-gradient-to-r ${getTypeColor(status.current_content.type)} transition-all duration-1000`}
                              style={{ width: `${status.contentProgress || 0}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-12 text-gray-500">
                        <span className="text-4xl mb-4 block">🎬</span>
                        <p>暂无播放内容</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Active Platforms */}
                <div className="bg-gray-800/50 rounded-2xl border border-white/5 overflow-hidden">
                  <div className="p-4 border-b border-white/5">
                    <h2 className="font-semibold flex items-center gap-2">
                      <span>🌐</span> 推流平台 ({enabledPlatforms.length})
                    </h2>
                  </div>
                  <div className="p-4 grid grid-cols-2 md:grid-cols-4 gap-3">
                    {enabledPlatforms.map((p, i) => (
                      <div key={i} className="bg-gray-700/50 rounded-xl p-3 flex items-center gap-3">
                        <span className="text-2xl">{getPlatformIcon(p.name)}</span>
                        <div>
                          <p className="font-medium">{p.name}</p>
                          <p className="text-xs text-emerald-400">● 推流中</p>
                        </div>
                      </div>
                    ))}
                    {enabledPlatforms.length === 0 && (
                      <div className="col-span-full text-center py-4 text-gray-500">
                        <p>未配置推流平台，请在"平台管理"中添加</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Control Panel */}
                <div className="bg-gray-800/50 rounded-2xl border border-white/5 overflow-hidden">
                  <div className="p-4 border-b border-white/5">
                    <h2 className="font-semibold flex items-center gap-2">
                      <span>🎛️</span> 导播控制
                    </h2>
                  </div>
                  <div className="p-4 flex flex-wrap gap-3">
                    <button
                      onClick={() => sendCommand("start")}
                      disabled={loading || status?.is_streaming}
                      className="px-6 py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-green-600 font-medium hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                      ▶️ 开始直播
                    </button>
                    <button
                      onClick={() => sendCommand("stop")}
                      disabled={loading || !status?.is_streaming}
                      className="px-6 py-3 rounded-xl bg-gradient-to-r from-red-500 to-rose-600 font-medium hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                      ⏹️ 停止直播
                    </button>
                    <button
                      onClick={() => sendCommand("next")}
                      disabled={loading || !status?.is_streaming}
                      className="px-6 py-3 rounded-xl bg-gradient-to-r from-blue-500 to-cyan-600 font-medium hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                      ⏭️ 下一个
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Platforms Tab */}
            {activeTab === "platforms" && (
              <div className="bg-gray-800/50 rounded-2xl border border-white/5 overflow-hidden">
                <div className="p-4 border-b border-white/5">
                  <h2 className="font-semibold flex items-center gap-2">
                    <span>🌐</span> 平台配置
                  </h2>
                  <p className="text-sm text-gray-400 mt-1">配置推流密钥后即可同时推流到多个平台</p>
                </div>
                <div className="divide-y divide-white/5">
                  {platforms.map((platform, index) => (
                    <div key={index} className="p-4 flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-gray-700 flex items-center justify-center text-2xl">
                        {getPlatformIcon(platform.name)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold">{platform.name}</h3>
                          {platform.enabled && platform.stream_key ? (
                            <span className="px-2 py-0.5 rounded text-xs bg-emerald-500/20 text-emerald-400">已配置</span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-xs bg-gray-700 text-gray-400">未配置</span>
                          )}
                        </div>
                        <p className="text-sm text-gray-500">{platform.rtmp_url}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <input
                          type="password"
                          placeholder="输入推流密钥"
                          className="px-3 py-2 rounded-lg bg-gray-700 border border-gray-600 text-sm w-40"
                          onChange={(e) => {
                            // Store in temp state
                          }}
                        />
                        <button
                          onClick={() => {
                            const input = document.querySelector(`input[data-platform="${platform.name}"]`) as HTMLInputElement;
                            if (input?.value) {
                              sendCommand("set_stream_key", { platform: platform.name.toLowerCase().replace(/[^a-z]/g, ''), stream_key: input.value });
                            }
                          }}
                          className="px-4 py-2 rounded-lg bg-blue-500/20 text-blue-400 text-sm hover:bg-blue-500/30"
                        >
                          保存
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Content Tab */}
            {activeTab === "content" && (
              <div className="bg-gray-800/50 rounded-2xl border border-white/5 overflow-hidden">
                <div className="p-4 border-b border-white/5">
                  <h2 className="font-semibold flex items-center gap-2">
                    <span>📋</span> 内容库 ({contentList.length} 项)
                  </h2>
                </div>
                <div className="max-h-[500px] overflow-y-auto">
                  <div className="divide-y divide-white/5">
                    {contentList.map((item, index) => (
                      <div 
                        key={index}
                        className={`p-4 flex items-center gap-4 hover:bg-white/5 cursor-pointer transition-all ${status?.current_content?.path === item.path ? 'bg-white/10' : ''}`}
                        onClick={() => status?.is_streaming && sendCommand("switch", { index })}
                      >
                        <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${getTypeColor(item.type)} flex items-center justify-center`}>
                          {getTypeIcon(item.type)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium truncate">{item.title || item.name}</p>
                          <p className="text-sm text-gray-500">
                            {item.artist && `${item.artist} • `}{formatTime(item.duration)}
                          </p>
                        </div>
                        <div className="text-xs text-gray-500">
                          {item.type === "news" ? "新闻" : item.type === "music" ? "音乐" : "视频"}
                        </div>
                        {status?.current_content?.path === item.path && (
                          <span className="text-emerald-400">🔊</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Tips */}
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4">
              <h3 className="font-semibold text-blue-400 mb-2">💡 多平台推流说明</h3>
              <ul className="text-sm text-gray-400 space-y-1">
                <li>• 支持 YouTube、TikTok、B站、抖音、快手等 10+ 平台</li>
                <li>• 使用 FFmpeg tee 模式，一次编码多路输出，节省服务器资源</li>
                <li>• 单个平台失败不影响其他平台，自动容错</li>
                <li>• 在"平台管理"中配置各平台的推流密钥即可启用</li>
              </ul>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
