"use client";

import { useEffect, useState, useCallback, useRef } from "react";

interface StreamStatus {
  success: boolean;
  isStreaming: boolean;
  ffmpegPid: number | null;
  uptime: string;
  cpuUsage: string;
  memoryUsage: string;
  videoPath: string;
  videoSize: string;
  newsCount: number;
  musicCount: number;
  playlistMode: boolean;
  totalPlaylistDuration: string;
  rtmpUrl: string;
  streamKey: string;
  timestamp: string;
  youtubeConnected?: boolean;
  streamHealth?: string;
  error?: string;
}

interface LogEntry {
  timestamp: string;
  level: "info" | "warning" | "error" | "success";
  message: string;
}

export default function Dashboard() {
  const [status, setStatus] = useState<StreamStatus>({
    success: false,
    isStreaming: false,
    ffmpegPid: null,
    uptime: "--:--:--",
    cpuUsage: "",
    memoryUsage: "",
    videoPath: "",
    videoSize: "",
    newsCount: 0,
    musicCount: 0,
    playlistMode: false,
    totalPlaylistDuration: "--:--:--",
    rtmpUrl: "",
    streamKey: "",
    timestamp: "",
  });
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [animatedCpu, setAnimatedCpu] = useState(0);
  const [animatedMemory, setAnimatedMemory] = useState(0);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [streamStats, setStreamStats] = useState({
    fps: 30,
    bitrate: "2500 kbps",
    resolution: "1080p"
  });
  const logContainerRef = useRef<HTMLDivElement>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch("/api/stream");
      const data = await response.json();
      setStatus(data);
      
      const cpuVal = parseFloat(data.cpuUsage) || 0;
      const memVal = parseFloat(data.memoryUsage) || 0;
      setAnimatedCpu(cpuVal);
      setAnimatedMemory(memVal);
    } catch (error) {
      console.error("Fetch error:", error);
    }
  }, []);

  const fetchLogs = useCallback(async () => {
    try {
      const response = await fetch("/api/logs?count=20");
      const data = await response.json();
      
      if (data.success && data.logs) {
        setLogs(data.logs);
        if (data.stats) {
          setStreamStats({
            fps: data.stats.fps || 30,
            bitrate: data.stats.bitrate || "2500 kbps",
            resolution: data.stats.resolution || "1080p"
          });
        }
      }
    } catch (error) {
      console.error("Fetch logs error:", error);
    }
  }, []);

  // SSE real-time log streaming
  const eventSourceRef = useRef<EventSource | null>(null);
  const [networkStatus, setNetworkStatus] = useState<string>("unknown");

  useEffect(() => {
    if (!autoRefresh) {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      return;
    }

    // Create SSE connection for real-time logs
    const connectSSE = () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      const eventSource = new EventSource('/api/logs?mode=stream');
      eventSourceRef.current = eventSource;

      eventSource.addEventListener('status', (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.networkStatus) {
            setNetworkStatus(data.networkStatus);
          }
        } catch {}
      });

      eventSource.addEventListener('logs', (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.data && Array.isArray(data.data)) {
            const newLogs: LogEntry[] = data.data.map((item: { timestamp: string; message: string }) => {
              let level: "info" | "warning" | "error" | "success" = "info";
              const msg = item.message.toLowerCase();
              if (msg.includes('error') || msg.includes('失败') || msg.includes('错误')) {
                level = "error";
              } else if (msg.includes('warning') || msg.includes('警告')) {
                level = "warning";
              } else if (msg.includes('success') || msg.includes('成功') || msg.includes('启动')) {
                level = "success";
              }
              // Parse timestamp from message if available
              const timeMatch = item.message.match(/\[(\d{2}:\d{2}:\d{2})\]/);
              return {
                timestamp: timeMatch ? timeMatch[1] : new Date().toLocaleTimeString("zh-CN", { hour12: false }),
                level,
                message: item.message.replace(/\[\d{2}:\d{2}:\d{2}\]\s*/, '')
              };
            });
            
            setLogs(prev => {
              const combined = [...prev, ...newLogs];
              // Keep last 100 logs
              return combined.slice(-100);
            });
          }
          if (data.networkStatus) {
            setNetworkStatus(data.networkStatus);
          }
        } catch {}
      });

      eventSource.onerror = () => {
        // Reconnect after 5 seconds
        setTimeout(connectSSE, 5000);
      };
    };

    connectSSE();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [autoRefresh]);

  useEffect(() => {
    fetchStatus();
    fetchLogs();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      fetchStatus();
      fetchLogs();
    }, 2000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchStatus, fetchLogs]);

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  const parseUptime = (uptime: string): number => {
    const parts = uptime.split(":").map(Number);
    if (parts.length === 3) {
      return parts[0] * 3600 + parts[1] * 60 + parts[2];
    }
    if (parts.length === 2) {
      return parts[0] * 60 + parts[1];
    }
    return 0;
  };

  const uptimeSeconds = parseUptime(status.uptime);
  const uptimeProgress = (uptimeSeconds % 3600) / 3600 * 100;

  const getLogColor = (level: string) => {
    switch (level) {
      case "error": return "text-red-400";
      case "warning": return "text-yellow-400";
      case "success": return "text-emerald-400";
      default: return "text-gray-400";
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0e17] flex flex-col overflow-hidden">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-br from-[#0a0e17] via-[#0f1624] to-[#0a0e17]" />
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl animate-blob" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-blob animation-delay-2000" />
        <div className="absolute top-1/2 left-1/2 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl animate-blob animation-delay-4000" />
        
        <div 
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), 
                              linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
            backgroundSize: '50px 50px'
          }}
        />
      </div>

      {/* Main Content Container */}
      <div className="relative z-10 flex flex-col min-h-screen">
        
        {/* Header */}
        <header className="px-6 py-4 border-b border-white/5 backdrop-blur-xl bg-black/20">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-4">
                <div className="relative">
                  <div className={`absolute inset-0 rounded-xl blur-md ${status.isStreaming ? 'bg-emerald-500/50' : 'bg-red-500/50'} animate-pulse`} />
                  <div className={`relative w-12 h-12 rounded-xl flex items-center justify-center ${status.isStreaming ? 'bg-gradient-to-br from-emerald-500 to-green-600' : 'bg-gradient-to-br from-red-500 to-rose-600'}`}>
                    <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  </div>
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white tracking-tight">YouTube 直播监控</h1>
                  <p className="text-sm text-gray-500">Digital Avatar Stream Dashboard</p>
                </div>
              </div>

              <div className={`hidden md:flex items-center gap-3 px-5 py-2.5 rounded-full border ${status.isStreaming ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-red-500/10 border-red-500/30'}`}>
                <div className="relative">
                  <div className={`w-3 h-3 rounded-full ${status.isStreaming ? 'bg-emerald-500' : 'bg-red-500'}`} />
                  {status.isStreaming && (
                    <>
                      <div className="absolute inset-0 rounded-full bg-emerald-500 animate-ping" />
                      <div className="absolute inset-0 rounded-full bg-emerald-500 animate-pulse" />
                    </>
                  )}
                </div>
                <span className={`font-semibold ${status.isStreaming ? 'text-emerald-400' : 'text-red-400'}`}>
                  {status.isStreaming ? 'LIVE' : 'OFFLINE'}
                </span>
                {status.isStreaming && (
                  <span className="flex items-center gap-1 text-gray-400 text-sm">
                    <span className="w-1 h-1 rounded-full bg-red-500 animate-pulse" />
                    <span className="w-1 h-1 rounded-full bg-red-500 animate-pulse animation-delay-200" />
                    <span className="w-1 h-1 rounded-full bg-red-500 animate-pulse animation-delay-400" />
                  </span>
                )}
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="hidden lg:block text-right">
                <p className="text-xs text-gray-500 uppercase tracking-wider">Last Update</p>
                <p className="text-sm font-mono text-white">
                  {status.timestamp ? new Date(status.timestamp).toLocaleTimeString("zh-CN") : "--:--:--"}
                </p>
              </div>

              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`relative px-5 py-2.5 rounded-xl font-medium text-sm transition-all duration-300 overflow-hidden ${autoRefresh ? 'text-white' : 'text-gray-400 border border-gray-700 hover:border-gray-600'}`}
              >
                {autoRefresh && (
                  <div className="absolute inset-0 bg-gradient-to-r from-emerald-600 to-green-600" />
                )}
                <span className="relative flex items-center gap-2">
                  <svg className={`w-4 h-4 ${autoRefresh ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  {autoRefresh ? 'Auto Refresh' : 'Paused'}
                </span>
              </button>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 p-6 overflow-auto">
          <div className="max-w-7xl mx-auto space-y-6">
            
            {/* Hero Status Section */}
            <div className={`relative rounded-2xl overflow-hidden ${status.isStreaming ? 'status-card-live' : 'status-card-offline'}`}>
              <div className="absolute inset-0 rounded-2xl">
                {status.isStreaming && (
                  <div className="absolute inset-[-2px] rounded-2xl bg-gradient-to-r from-emerald-500 via-green-400 to-emerald-500 animate-border-rotate opacity-50" />
                )}
              </div>
              
              <div className={`relative m-[2px] rounded-xl p-6 md:p-8 ${status.isStreaming ? 'bg-gradient-to-r from-emerald-950/90 via-green-950/80 to-emerald-950/90' : 'bg-gradient-to-r from-red-950/90 via-rose-950/80 to-red-950/90'}`}>
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                  <div className="flex items-center gap-6">
                    <div className={`relative w-20 h-20 md:w-24 md:h-24 rounded-2xl flex items-center justify-center ${status.isStreaming ? 'bg-gradient-to-br from-emerald-500/20 to-green-600/20' : 'bg-gradient-to-br from-red-500/20 to-rose-600/20'}`}>
                      {status.isStreaming && (
                        <>
                          <div className="absolute inset-0 rounded-2xl border-2 border-emerald-500/30 animate-ping" />
                          <div className="absolute inset-[-8px] rounded-3xl border border-emerald-500/20 animate-pulse" />
                        </>
                      )}
                      
                      {status.isStreaming ? (
                        <svg className="w-10 h-10 md:w-12 md:h-12 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5.636 18.364a9 9 0 010-12.728m12.728 0a9 9 0 010 12.728m-9.9-2.829a5 5 0 010-7.07m7.072 0a5 5 0 010 7.07M13 12a1 1 0 11-2 0 1 1 0 012 0z" />
                        </svg>
                      ) : (
                        <svg className="w-10 h-10 md:w-12 md:h-12 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414" />
                        </svg>
                      )}
                    </div>

                    <div>
                      <h2 className="text-2xl md:text-3xl font-bold text-white mb-1">
                        Stream {status.isStreaming ? 'Active' : 'Inactive'}
                      </h2>
                      <p className="text-gray-400 text-lg">
                        {status.isStreaming ? `Running for ${status.uptime}` : 'Waiting to start...'}
                      </p>
                      {status.isStreaming && (
                        <div className="mt-3 flex items-center gap-4">
                          <div className="flex items-center gap-2 text-sm">
                            <span className="text-gray-500">PID:</span>
                            <span className="px-3 py-1 bg-black/30 rounded-lg font-mono text-emerald-400">{status.ffmpegPid}</span>
                          </div>
                          <div className="flex items-center gap-2 text-sm">
                            <span className="text-gray-500">FPS:</span>
                            <span className="px-3 py-1 bg-emerald-500/20 rounded-lg text-emerald-400">{streamStats.fps}</span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {status.isStreaming && (
                    <div className="grid grid-cols-2 gap-4 md:gap-6">
                      <div className="text-center">
                        <div className="relative w-20 h-20 mx-auto">
                          <svg className="w-20 h-20 transform -rotate-90">
                            <circle cx="40" cy="40" r="35" stroke="currentColor" strokeWidth="4" fill="none" className="text-gray-800" />
                            <circle 
                              cx="40" cy="40" r="35" 
                              stroke="currentColor" 
                              strokeWidth="4" 
                              fill="none" 
                              className="text-emerald-500"
                              strokeDasharray={`${uptimeProgress * 2.2} 220`}
                              strokeLinecap="round"
                            />
                          </svg>
                          <div className="absolute inset-0 flex items-center justify-center">
                            <span className="text-lg font-bold text-white">{status.uptime.split(':')[0]}h</span>
                          </div>
                        </div>
                        <p className="text-xs text-gray-500 mt-2">Uptime</p>
                      </div>

                      <div className="text-center">
                        <div className="relative w-20 h-20 mx-auto">
                          <svg className="w-20 h-20 transform -rotate-90">
                            <circle cx="40" cy="40" r="35" stroke="currentColor" strokeWidth="4" fill="none" className="text-gray-800" />
                            <circle 
                              cx="40" cy="40" r="35" 
                              stroke="currentColor" 
                              strokeWidth="4" 
                              fill="none" 
                              className="text-blue-500"
                              strokeDasharray="198 220"
                              strokeLinecap="round"
                            />
                          </svg>
                          <div className="absolute inset-0 flex items-center justify-center">
                            <span className="text-lg font-bold text-white">{streamStats.resolution}</span>
                          </div>
                        </div>
                        <p className="text-xs text-gray-500 mt-2">Quality</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
              <div className="group relative rounded-2xl overflow-hidden bg-gradient-to-br from-gray-900/80 to-gray-800/50 border border-white/5 hover:border-blue-500/30 transition-all duration-300">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="relative p-5">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center">
                      <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                      </svg>
                    </div>
                    <span className="text-xs text-gray-500 uppercase tracking-wider">CPU</span>
                  </div>
                  <div className="space-y-2">
                    <p className="text-3xl font-bold text-white">{status.cpuUsage || '--'}<span className="text-lg text-gray-500">%</span></p>
                    <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full transition-all duration-500"
                        style={{ width: `${Math.min(animatedCpu, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div className="group relative rounded-2xl overflow-hidden bg-gradient-to-br from-gray-900/80 to-gray-800/50 border border-white/5 hover:border-purple-500/30 transition-all duration-300">
                <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="relative p-5">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center">
                      <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                      </svg>
                    </div>
                    <span className="text-xs text-gray-500 uppercase tracking-wider">Memory</span>
                  </div>
                  <div className="space-y-2">
                    <p className="text-3xl font-bold text-white">{status.memoryUsage || '--'}<span className="text-lg text-gray-500">%</span></p>
                    <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-purple-500 to-pink-400 rounded-full transition-all duration-500"
                        style={{ width: `${Math.min(animatedMemory, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div className="group relative rounded-2xl overflow-hidden bg-gradient-to-br from-gray-900/80 to-gray-800/50 border border-white/5 hover:border-orange-500/30 transition-all duration-300">
                <div className="absolute inset-0 bg-gradient-to-br from-orange-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="relative p-5">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-10 h-10 rounded-xl bg-orange-500/10 flex items-center justify-center">
                      <svg className="w-5 h-5 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
                      </svg>
                    </div>
                    <span className="text-xs text-gray-500 uppercase tracking-wider">Bitrate</span>
                  </div>
                  <div className="space-y-2">
                    <p className="text-2xl font-bold text-white">{streamStats.bitrate}</p>
                    <p className="text-xs text-gray-500">Video bitrate</p>
                  </div>
                </div>
              </div>

              <div className="group relative rounded-2xl overflow-hidden bg-gradient-to-br from-gray-900/80 to-gray-800/50 border border-white/5 hover:border-emerald-500/30 transition-all duration-300">
                <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="relative p-5">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                      <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                      </svg>
                    </div>
                    <span className="text-xs text-gray-500 uppercase tracking-wider">News</span>
                  </div>
                  <div className="space-y-2">
                    <p className="text-3xl font-bold text-white">{status.newsCount}<span className="text-lg text-gray-500"> 条</span></p>
                    <p className="text-xs text-gray-500">新闻条目</p>
                  </div>
                </div>
              </div>

              <div className="group relative rounded-2xl overflow-hidden bg-gradient-to-br from-gray-900/80 to-gray-800/50 border border-white/5 hover:border-pink-500/30 transition-all duration-300">
                <div className="absolute inset-0 bg-gradient-to-br from-pink-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="relative p-5">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-10 h-10 rounded-xl bg-pink-500/10 flex items-center justify-center">
                      <svg className="w-5 h-5 text-pink-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                      </svg>
                    </div>
                    <span className="text-xs text-gray-500 uppercase tracking-wider">Music</span>
                  </div>
                  <div className="space-y-2">
                    <p className="text-3xl font-bold text-white">{status.musicCount || 0}<span className="text-lg text-gray-500"> 首</span></p>
                    <p className="text-xs text-gray-500">流行歌曲</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Live Logs Section - 实时日志 */}
            <div className="rounded-2xl bg-gradient-to-br from-gray-900/80 to-gray-800/50 border border-white/5 overflow-hidden">
              <div className="px-6 py-4 border-b border-white/5 bg-black/20">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center">
                      <svg className="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-white">Live Console</h3>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${status.isStreaming ? 'bg-emerald-500/20 text-emerald-400' : 'bg-gray-700 text-gray-400'}`}>
                      {status.isStreaming ? 'STREAMING' : 'IDLE'}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span>RTMP: {networkStatus === 'connected' ? '✅ Connected' : networkStatus === 'closing' ? '⚠️ Closing' : networkStatus === 'disconnected' ? '❌ Disconnected' : '⏳ Checking...'}</span>
                    <span>Health: <span className={status.streamHealth === 'healthy' ? 'text-emerald-400' : status.streamHealth === 'warning' ? 'text-yellow-400' : 'text-red-400'}>{status.streamHealth || 'unknown'}</span></span>
                  </div>
                </div>
              </div>
              
              <div className="p-4">
                <div 
                  ref={logContainerRef}
                  className="bg-black/60 rounded-xl p-4 font-mono text-xs h-64 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent"
                >
                  {logs.length > 0 ? (
                    <div className="space-y-1">
                      {logs.map((log, index) => (
                        <div key={index} className="flex items-start gap-2 hover:bg-white/5 px-1 rounded transition-colors">
                          <span className="text-gray-600 shrink-0 select-none">[{log.timestamp}]</span>
                          <span className={getLogColor(log.level)}>{log.message}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="flex items-center justify-center h-full text-gray-500">
                      <div className="text-center">
                        <div className={`w-3 h-3 rounded-full mx-auto mb-2 ${status.isStreaming ? 'bg-emerald-500 animate-pulse' : 'bg-gray-600'}`} />
                        <p>{status.isStreaming ? 'Connecting to log stream...' : 'Stream not active - Start streaming to see logs'}</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </main>

        {/* Footer */}
        <footer className="px-6 py-4 border-t border-white/5 bg-black/20 backdrop-blur-xl">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${status.isStreaming ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
                <span className="text-sm text-gray-500">
                  {status.isStreaming ? 'System Normal' : 'Service Stopped'}
                </span>
              </div>
              <div className="hidden md:flex items-center gap-4 text-sm text-gray-600">
                <span>Refresh: 2s</span>
                <span>•</span>
                <span>Version 1.1.0</span>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">
                {status.timestamp ? new Date(status.timestamp).toLocaleString("zh-CN") : '--'}
              </span>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
