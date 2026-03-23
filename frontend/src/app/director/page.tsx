"use client";

import { useEffect, useState, useCallback } from "react";
import { directorApi, platformApi, layerApi } from "@/lib/api";
import HLSPlayer from "@/components/HLSPlayer";
import {
  ContentSelector,
  LayerManager,
  DanmakuPanel,
  PlaybackControls,
  ContentItem,
  Layer,
  DanmakuMessage,
  AISuggestion,
} from "@/components/director";

// 默认 HLS 测试流
const DEFAULT_PREVIEW_URL = "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8";

// Mock 弹幕数据
const MOCK_DANMAKU: DanmakuMessage[] = [
  { id: "1", user: "小明", content: "主播好！第一次来", platform: "bilibili", timestamp: Date.now() - 60000 },
  { id: "2", user: "Alice", content: "Can you play some jazz music?", platform: "youtube", timestamp: Date.now() - 45000 },
  { id: "3", user: "抖音用户", content: "切首歌吧", platform: "douyin", timestamp: Date.now() - 30000 },
  { id: "4", user: "观众甲", content: "放周杰伦的歌", platform: "bilibili", timestamp: Date.now() - 15000 },
  { id: "5", user: "Viewer", content: "switch to next video please", platform: "youtube", timestamp: Date.now() - 5000 },
];

// Mock AI 建议
const MOCK_SUGGESTIONS: AISuggestion[] = [
  {
    id: "s1",
    type: "switch_content",
    confidence: 0.92,
    message: MOCK_DANMAKU[3],
    action: { type: "switch_music", target: "周杰伦" },
    reply: "检测到用户想听周杰伦的歌，是否切换？",
  },
];

interface Platform {
  platform_type: string;
  display_name: string;
  rtmp_url: string;
  has_stream_key: boolean;
  enabled: boolean;
  status: string;
  last_error: string | null;
}

interface DirectorStatus {
  is_running: boolean;
  current_content: string | null;
  content_queue: ContentItem[];
  uptime: number;
}

interface CompositionStatus {
  is_running: boolean;
  layer_count: number;
  hls_url: string | null;
}

export default function DirectorDashboard() {
  // 播放状态
  const [status, setStatus] = useState<DirectorStatus | null>(null);
  const [loading, setLoading] = useState(false);

  // 内容和图层
  const [contentList, setContentList] = useState<ContentItem[]>([]);
  const [currentContent, setCurrentContent] = useState<ContentItem | null>(null);
  const [layers, setLayers] = useState<Layer[]>([]);

  // 预览
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewPoster, setPreviewPoster] = useState<string | null>(null);
  const [previewTitle, setPreviewTitle] = useState<string>("");

  // 合成状态
  const [compositionStatus, setCompositionStatus] = useState<CompositionStatus | null>(null);
  const [useCompositedStream, setUseCompositedStream] = useState(false);

  // 弹幕和 AI
  const [danmakuMessages, setDanmakuMessages] = useState<DanmakuMessage[]>(MOCK_DANMAKU);
  const [aiSuggestions, setAiSuggestions] = useState<AISuggestion[]>(MOCK_SUGGESTIONS);
  const [autoMode, setAutoMode] = useState(false);

  // 平台
  const [platforms, setPlatforms] = useState<Platform[]>([]);

  // 左侧面板 Tab
  const [leftTab, setLeftTab] = useState<"content" | "layers">("content");

  // 稳定的回调
  const handlePlayerError = useCallback((err: string) => {
    console.error("HLS Player error:", err);
  }, []);

  // 获取状态
  const fetchStatus = useCallback(async () => {
    try {
      const data = await directorApi.getStatus();
      setStatus(data);
    } catch (error) {
      console.error("Fetch status error:", error);
    }
  }, []);

  // 获取内容列表
  const fetchContentList = useCallback(async () => {
    try {
      const data = await directorApi.getQueue();
      if (data.queue) {
        setContentList(data.queue);
      }
    } catch (error) {
      console.error("Fetch content list error:", error);
    }
  }, []);

  // 获取平台
  const fetchPlatforms = useCallback(async () => {
    try {
      const data = await platformApi.list();
      if (data.platforms) {
        setPlatforms(Object.values(data.platforms) as Platform[]);
      }
    } catch (error) {
      console.error("Fetch platforms error:", error);
    }
  }, []);

  // 获取图层列表
  const fetchLayers = useCallback(async () => {
    try {
      const data = await layerApi.list();
      if (data.layers) {
        setLayers(data.layers as Layer[]);
      }
    } catch (error) {
      console.error("Fetch layers error:", error);
    }
  }, []);

  // 获取合成状态
  const fetchCompositionStatus = useCallback(async () => {
    try {
      const data = await layerApi.getCompositionStatus();
      setCompositionStatus(data);
      return data;
    } catch (error) {
      console.error("Fetch composition status error:", error);
      return null;
    }
  }, []);

  // 初始化
  useEffect(() => {
    fetchStatus();
    fetchContentList();
    fetchPlatforms();
    fetchLayers();
    fetchCompositionStatus();
  }, [fetchStatus, fetchContentList, fetchPlatforms, fetchLayers, fetchCompositionStatus]);

  // 自动刷新
  useEffect(() => {
    const interval = setInterval(() => {
      fetchStatus();
      if (useCompositedStream) {
        fetchCompositionStatus();
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchStatus, fetchCompositionStatus, useCompositedStream]);

  // 发送命令
  const sendCommand = async (action: string) => {
    setLoading(true);
    try {
      let result;
      switch (action) {
        case "start":
          result = await directorApi.start();
          if (result.success) {
            // 设置预览
            if (contentList.length > 0) {
              const firstContent = contentList.find(c => c.url);
              if (firstContent?.url) {
                setPreviewUrl(firstContent.url);
                setPreviewPoster(firstContent.thumbnail || null);
                setPreviewTitle(firstContent.title);
                setCurrentContent(firstContent);
              } else {
                setPreviewUrl(DEFAULT_PREVIEW_URL);
                setPreviewTitle("Big Buck Bunny - 开源动画短片");
              }
            } else {
              setPreviewUrl(DEFAULT_PREVIEW_URL);
              setPreviewTitle("Big Buck Bunny - 开源动画短片");
            }
          }
          break;
        case "stop":
          result = await directorApi.stop();
          setPreviewUrl(null);
          // 同时停止图层合成
          if (useCompositedStream) {
            await layerApi.stopComposition();
            setUseCompositedStream(false);
          }
          break;
        case "next":
          result = await directorApi.switchContent({ content_type: "next" });
          break;
        default:
          result = { error: "Unknown action" };
      }
      console.log("Command result:", result);
      await fetchStatus();
      return result;
    } catch (error) {
      console.error("Command error:", error);
      return { error: String(error) };
    } finally {
      setLoading(false);
    }
  };

  // 启动图层合成
  const startComposition = async () => {
    setLoading(true);
    try {
      const result = await layerApi.startComposition();
      if (result.success) {
        setUseCompositedStream(true);
        // 使用合成后的 HLS 流
        setPreviewUrl(result.hls_url);
        setPreviewTitle("合成视频流 (多图层)");
        await fetchCompositionStatus();
      }
      return result;
    } catch (error) {
      console.error("Start composition error:", error);
      return { error: String(error) };
    } finally {
      setLoading(false);
    }
  };

  // 停止图层合成
  const stopComposition = async () => {
    setLoading(true);
    try {
      const result = await layerApi.stopComposition();
      setUseCompositedStream(false);
      // 切换回默认预览
      setPreviewUrl(DEFAULT_PREVIEW_URL);
      setPreviewTitle("Big Buck Bunny");
      await fetchCompositionStatus();
      return result;
    } catch (error) {
      console.error("Stop composition error:", error);
      return { error: String(error) };
    } finally {
      setLoading(false);
    }
  };

  // 选择内容
  const handleSelectContent = (item: ContentItem) => {
    if (item.url) {
      setPreviewUrl(item.url);
      setPreviewPoster(item.thumbnail || null);
      setPreviewTitle(item.title);
      setCurrentContent(item);
    } else {
      setPreviewUrl(DEFAULT_PREVIEW_URL);
      setPreviewTitle(item.title + " (默认流)");
    }
  };

  // 图层操作 - 调用后端 API
  const handleToggleLayerVisibility = async (layerId: string) => {
    const layer = layers.find(l => l.id === layerId);
    if (layer) {
      try {
        await layerApi.update(layerId, { visible: !layer.visible });
        setLayers(prev => prev.map(l => 
          l.id === layerId ? { ...l, visible: !l.visible } : l
        ));
        // 如果正在合成，重启以应用更改
        if (useCompositedStream && compositionStatus?.is_running) {
          await layerApi.stopComposition();
          await layerApi.startComposition();
        }
      } catch (error) {
        console.error("Toggle visibility error:", error);
      }
    }
  };

  const handleReorderLayers = async (layerIds: string[]) => {
    try {
      await layerApi.reorder(layerIds);
      // 更新本地状态
      setLayers(prev => {
        const layerMap = new Map(prev.map(l => [l.id, l]));
        return layerIds.map((id, i) => {
          const layer = layerMap.get(id);
          return layer ? { ...layer, order: i } : null;
        }).filter(Boolean) as Layer[];
      });
    } catch (error) {
      console.error("Reorder layers error:", error);
    }
  };

  const handleRemoveLayer = async (layerId: string) => {
    try {
      await layerApi.remove(layerId);
      setLayers(prev => prev.filter(l => l.id !== layerId));
    } catch (error) {
      console.error("Remove layer error:", error);
    }
  };

  const handleAddLayer = async (type: Layer["type"]) => {
    // 创建新图层
    const newLayerId = `layer_${Date.now()}`;
    const sourceMap: Record<string, string> = {
      video: "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
      image: "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=200",
      text: "示例文字",
      audio: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
    };

    const typeNameMap: Record<string, string> = {
      video: "视频",
      image: "图片",
      text: "文字",
      audio: "音频",
    };

    try {
      await layerApi.add({
        id: newLayerId,
        type: type as any,
        name: `新${typeNameMap[type]}图层`,
        source: sourceMap[type],
        visible: true,
        order: layers.length,
      });
      // 刷新图层列表
      await fetchLayers();
    } catch (error) {
      console.error("Add layer error:", error);
    }
  };

  // 弹幕操作
  const handleSendMessage = (message: string) => {
    const newMessage: DanmakuMessage = {
      id: `m${Date.now()}`,
      user: "主播",
      content: message,
      platform: "other",
      timestamp: Date.now(),
    };
    setDanmakuMessages(prev => [...prev, newMessage]);
  };

  const handleAcceptSuggestion = (suggestion: AISuggestion) => {
    console.log("Accepting suggestion:", suggestion);
    setAiSuggestions(prev => prev.filter(s => s.id !== suggestion.id));
    if (suggestion.reply) {
      handleSendMessage(suggestion.reply);
    }
  };

  const handleDismissSuggestion = (suggestionId: string) => {
    setAiSuggestions(prev => prev.filter(s => s.id !== suggestionId));
  };

  // 格式化时间
  const formatTime = (seconds: number): string => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return h > 0 ? `${h}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}` : `${m}:${s.toString().padStart(2, "0")}`;
  };

  const enabledPlatforms = platforms.filter(p => p.enabled && p.has_stream_key);

  return (
    <div className="h-screen bg-[#0a0e17] text-white flex flex-col overflow-hidden">
      {/* 背景效果 */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-br from-[#0a0e17] via-[#0f1624] to-[#0a0e17]" />
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 h-full flex flex-col">
        {/* 顶部标题栏 */}
        <header className="px-4 py-3 border-b border-white/5 backdrop-blur-xl bg-black/20 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                status?.is_running || compositionStatus?.is_running ? 'bg-gradient-to-br from-emerald-500 to-green-600' : 'bg-gradient-to-br from-gray-600 to-gray-700'
              }`}>
                <span className="text-xl">🎬</span>
              </div>
              <div>
                <h1 className="text-lg font-bold">智能导播台</h1>
                <p className="text-xs text-gray-400">多平台直播 · 图层合成 · AI 互动</p>
              </div>
              <div className={`ml-4 px-3 py-1 rounded-full text-xs font-medium ${
                status?.is_running || compositionStatus?.is_running ? 'bg-emerald-500/20 text-emerald-400' : 'bg-gray-700 text-gray-400'
              }`}>
                {useCompositedStream ? `🎨 合成中 (${layers.filter(l => l.visible).length}层)` : 
                 status?.is_running ? `🔴 推流中 → ${enabledPlatforms.length}平台` : '⏸️ 待机'}
              </div>
            </div>
            
            <div className="flex items-center gap-3 text-sm">
              <div className="text-right">
                <p className="text-xs text-gray-500">运行时长</p>
                <p className="font-mono">{formatTime(status?.uptime || 0)}</p>
              </div>
              {useCompositedStream && (
                <span className="text-xs bg-purple-500/20 text-purple-400 px-2 py-1 rounded">
                  FFmpeg 合成
                </span>
              )}
            </div>
          </div>
        </header>

        {/* 主内容区 - 三栏布局 */}
        <div className="flex-1 flex overflow-hidden">
          {/* 左侧控制面板 */}
          <aside className="w-64 lg:w-72 flex-shrink-0 border-r border-white/5 bg-black/10 flex flex-col">
            {/* Tab 切换 */}
            <div className="p-2 border-b border-white/5 flex gap-1">
              <button
                onClick={() => setLeftTab("content")}
                className={`flex-1 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  leftTab === "content" ? 'bg-emerald-500/20 text-emerald-400' : 'text-gray-400 hover:bg-white/5'
                }`}
              >
                📋 内容
              </button>
              <button
                onClick={() => setLeftTab("layers")}
                className={`flex-1 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  leftTab === "layers" ? 'bg-emerald-500/20 text-emerald-400' : 'text-gray-400 hover:bg-white/5'
                }`}
              >
                📑 图层 {layers.length > 0 && `(${layers.length})`}
              </button>
            </div>

            {/* 内容/图层选择 */}
            <div className="flex-1 overflow-hidden">
              {leftTab === "content" ? (
                <ContentSelector
                  contents={contentList}
                  currentContent={currentContent}
                  onSelect={handleSelectContent}
                />
              ) : (
                <LayerManager
                  layers={layers}
                  onToggleVisibility={handleToggleLayerVisibility}
                  onReorder={handleReorderLayers}
                  onRemove={handleRemoveLayer}
                  onAddLayer={handleAddLayer}
                />
              )}
            </div>

            {/* 播放控制 */}
            <div className="border-t border-white/5 flex-shrink-0">
              <PlaybackControls
                isPlaying={status?.is_running || compositionStatus?.is_running || false}
                loading={loading}
                onStart={() => {
                  // 如果有图层，启动合成模式
                  if (layers.length > 0 && !useCompositedStream) {
                    startComposition();
                  } else {
                    sendCommand("start");
                  }
                }}
                onStop={() => {
                  if (useCompositedStream) {
                    stopComposition();
                  } else {
                    sendCommand("stop");
                  }
                }}
                onNext={() => sendCommand("next")}
                platforms={platforms}
              />
            </div>
          </aside>

          {/* 中间视频预览 */}
          <main className="flex-1 flex flex-col overflow-hidden min-w-0">
            {/* 预览区域 */}
            <div className="flex-1 p-4 min-h-0">
              <div className="h-full bg-gray-800/50 rounded-2xl border border-white/5 overflow-hidden flex flex-col">
                {/* 预览标题 */}
                <div className="p-3 border-b border-white/5 flex items-center justify-between flex-shrink-0">
                  <h2 className="font-medium text-sm flex items-center gap-2">
                    <span>🎥</span> 
                    {useCompositedStream ? "合成视频流" : "本地预览"}
                    {previewTitle && (
                      <span className="text-gray-400 font-normal">- {previewTitle}</span>
                    )}
                  </h2>
                  <div className="flex items-center gap-2">
                    {previewUrl && status?.is_running && (
                      <span className="text-xs text-emerald-400 flex items-center gap-1">
                        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                        {useCompositedStream ? "合成" : "LIVE"}
                      </span>
                    )}
                    {useCompositedStream && (
                      <span className="text-xs text-purple-400">
                        {layers.filter(l => l.visible).length} 图层活跃
                      </span>
                    )}
                  </div>
                </div>

                {/* 视频播放器 */}
                <div className="flex-1 bg-black relative min-h-0">
                  {previewUrl ? (
                    <HLSPlayer
                      key={previewUrl}
                      src={previewUrl}
                      poster={previewPoster || undefined}
                      autoPlay
                      muted={false}
                      className="w-full h-full"
                      onError={handlePlayerError}
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <div className="text-center text-gray-500">
                        <div className="w-20 h-20 rounded-full bg-gray-700/50 flex items-center justify-center mx-auto mb-4">
                          <span className="text-4xl">🎬</span>
                        </div>
                        <p>点击"开始"预览视频流</p>
                        <p className="text-xs mt-2 text-gray-600">支持多图层合成、弹幕互动</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* 状态信息栏 */}
            <div className="px-4 pb-4 flex-shrink-0">
              <div className="grid grid-cols-6 gap-2">
                {[
                  { label: "状态", value: useCompositedStream ? "🎨 合成" : status?.is_running ? "✅ 运行" : "⏸️ 待机", color: status?.is_running || useCompositedStream ? "text-emerald-400" : "" },
                  { label: "帧率", value: "30 FPS", color: "" },
                  { label: "码率", value: "2500 kbps", color: "" },
                  { label: "时长", value: formatTime(status?.uptime || 0), color: "" },
                  { label: "图层", value: `${layers.filter(l => l.visible).length}/${layers.length}`, color: layers.length > 0 ? "text-purple-400" : "" },
                  { label: "平台", value: `${enabledPlatforms.length} 个`, color: enabledPlatforms.length > 0 ? "text-emerald-400" : "" },
                ].map((item, i) => (
                  <div key={i} className="bg-gray-800/50 rounded-lg p-2 text-center">
                    <p className="text-xs text-gray-500">{item.label}</p>
                    <p className={`text-sm font-medium ${item.color}`}>{item.value}</p>
                  </div>
                ))}
              </div>
            </div>
          </main>

          {/* 右侧弹幕面板 */}
          <aside className="w-72 lg:w-80 flex-shrink-0 border-l border-white/5 bg-black/10">
            <DanmakuPanel
              messages={danmakuMessages}
              suggestions={aiSuggestions}
              onSendMessage={handleSendMessage}
              onAcceptSuggestion={handleAcceptSuggestion}
              onDismissSuggestion={handleDismissSuggestion}
              autoMode={autoMode}
              onToggleAutoMode={() => setAutoMode(!autoMode)}
            />
          </aside>
        </div>
      </div>
    </div>
  );
}
