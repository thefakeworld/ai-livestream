"use client";

import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import Hls from "hls.js";

interface HLSPlayerProps {
  src: string;
  poster?: string;
  autoPlay?: boolean;
  muted?: boolean;
  className?: string;
  onReady?: () => void;
  onError?: (error: string) => void;
}

export default function HLSPlayer({
  src,
  poster,
  autoPlay = true,
  muted = true,
  className = "",
  onReady,
  onError,
}: HLSPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const hlsRef = useRef<Hls | null>(null);
  const prevSrcRef = useRef<string>("");
  
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [volume, setVolume] = useState(muted ? 0 : 0.8);
  const [isMuted, setIsMuted] = useState(muted);
  const [showControls, setShowControls] = useState(true);
  const controlsTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // 稳定的回调引用
  const onReadyRef = useRef(onReady);
  const onErrorRef = useRef(onError);
  
  useEffect(() => {
    onReadyRef.current = onReady;
    onErrorRef.current = onError;
  }, [onReady, onError]);

  // 初始化 HLS 播放器 - 只在 src 变化时重新创建
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !src) return;

    // 如果 src 没有变化，不重新创建
    if (prevSrcRef.current === src && hlsRef.current) {
      return;
    }
    prevSrcRef.current = src;

    // 清理之前的实例
    if (hlsRef.current) {
      hlsRef.current.destroy();
      hlsRef.current = null;
    }

    setIsLoading(true);
    setError(null);
    setIsPlaying(false);

    // 判断是否是 HLS 流
    const isHLS = src.includes(".m3u8") || src.includes("m3u8");

    if (isHLS && Hls.isSupported()) {
      // 使用 HLS.js
      const hls = new Hls({
        enableWorker: true,
        lowLatencyMode: true,
        backBufferLength: 90,
        maxBufferLength: 30,
        maxMaxBufferLength: 60,
      });

      hls.loadSource(src);
      hls.attachMedia(video);

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        setIsLoading(false);
        if (autoPlay) {
          video.play().catch(() => {});
        }
        onReadyRef.current?.();
      });

      hls.on(Hls.Events.ERROR, (_, data) => {
        if (data.fatal) {
          setIsLoading(false);
          const errorMsg = `HLS Error: ${data.type} - ${data.details}`;
          setError(errorMsg);
          onErrorRef.current?.(errorMsg);

          // 尝试恢复
          switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              console.log("Network error, trying to recover...");
              hls.startLoad();
              break;
            case Hls.ErrorTypes.MEDIA_ERROR:
              console.log("Media error, trying to recover...");
              hls.recoverMediaError();
              break;
            default:
              console.log("Fatal error, destroying HLS instance");
              hls.destroy();
              break;
          }
        }
      });

      hlsRef.current = hls;
    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
      // Safari 原生 HLS 支持
      video.src = src;
      video.addEventListener("loadedmetadata", () => {
        setIsLoading(false);
        if (autoPlay) {
          video.play().catch(() => {});
        }
        onReadyRef.current?.();
      }, { once: true });
    } else if (!isHLS) {
      // 非 HLS 视频，直接播放
      video.src = src;
      video.addEventListener("loadeddata", () => {
        setIsLoading(false);
        if (autoPlay) {
          video.play().catch(() => {});
        }
        onReadyRef.current?.();
      }, { once: true });
    } else {
      setIsLoading(false);
      setError("HLS is not supported in this browser");
      onErrorRef.current?.("HLS is not supported in this browser");
    }

    // 播放状态监听
    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    const handleWaiting = () => setIsLoading(true);
    const handlePlaying = () => setIsLoading(false);

    video.addEventListener("play", handlePlay);
    video.addEventListener("pause", handlePause);
    video.addEventListener("waiting", handleWaiting);
    video.addEventListener("playing", handlePlaying);

    return () => {
      video.removeEventListener("play", handlePlay);
      video.removeEventListener("pause", handlePause);
      video.removeEventListener("waiting", handleWaiting);
      video.removeEventListener("playing", handlePlaying);
    };
  }, [src, autoPlay]); // 只依赖 src 和 autoPlay

  // 设置初始音量
  useEffect(() => {
    const video = videoRef.current;
    if (video) {
      video.volume = volume;
      video.muted = isMuted;
    }
  }, []); // 只在挂载时设置一次

  // 播放/暂停
  const handlePlayPause = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;

    if (video.paused) {
      video.play();
    } else {
      video.pause();
    }
  }, []);

  // 全屏
  const handleFullscreen = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;

    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      video.requestFullscreen();
    }
  }, []);

  // 音量调节
  const handleVolumeChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const video = videoRef.current;
    if (!video) return;
    
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    video.volume = newVolume;
    
    if (newVolume > 0) {
      setIsMuted(false);
      video.muted = false;
    }
  }, []);

  // 静音切换
  const toggleMute = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;
    
    const newMuted = !isMuted;
    setIsMuted(newMuted);
    video.muted = newMuted;
  }, [isMuted]);

  // 显示控制条（鼠标移动时）
  const showControlsTemporarily = useCallback(() => {
    setShowControls(true);
    
    if (controlsTimeoutRef.current) {
      clearTimeout(controlsTimeoutRef.current);
    }
    
    controlsTimeoutRef.current = setTimeout(() => {
      if (isPlaying) {
        setShowControls(false);
      }
    }, 3000);
  }, [isPlaying]);

  // 清理定时器
  useEffect(() => {
    return () => {
      if (controlsTimeoutRef.current) {
        clearTimeout(controlsTimeoutRef.current);
      }
    };
  }, []);

  // 清理 HLS 实例
  useEffect(() => {
    return () => {
      if (hlsRef.current) {
        hlsRef.current.destroy();
        hlsRef.current = null;
      }
    };
  }, []);

  // 音量图标
  const volumeIcon = useMemo(() => {
    if (isMuted || volume === 0) return "🔇";
    if (volume < 0.3) return "🔈";
    if (volume < 0.7) return "🔉";
    return "🔊";
  }, [isMuted, volume]);

  return (
    <div 
      className={`relative bg-black group ${className}`}
      onMouseMove={showControlsTemporarily}
      onMouseLeave={() => isPlaying && setShowControls(false)}
    >
      <video
        ref={videoRef}
        className="w-full h-full object-contain"
        poster={poster}
        playsInline
      />

      {/* Loading overlay */}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/50 z-10">
          <div className="flex flex-col items-center gap-2">
            <div className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-white text-sm">加载中...</p>
          </div>
        </div>
      )}

      {/* Error overlay */}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/70 z-20">
          <div className="text-center p-4">
            <span className="text-red-500 text-4xl mb-2 block">⚠️</span>
            <p className="text-white text-sm">{error}</p>
            <button
              onClick={() => {
                setError(null);
                setIsLoading(true);
                prevSrcRef.current = ""; // 强制重新加载
                // Trigger reload
                const video = videoRef.current;
                if (video) {
                  video.load();
                }
              }}
              className="mt-2 px-4 py-2 bg-emerald-500 text-white rounded-lg text-sm hover:bg-emerald-600"
            >
              重试
            </button>
          </div>
        </div>
      )}

      {/* Controls overlay - 只在需要时显示 */}
      <div 
        className={`absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent p-4 transition-opacity duration-300 z-10 ${
          showControls || !isPlaying ? 'opacity-100' : 'opacity-0'
        }`}
      >
        {/* 进度条区域（可选） */}
        
        <div className="flex items-center gap-3">
          {/* 播放/暂停 */}
          <button
            onClick={handlePlayPause}
            className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center hover:bg-white/30 transition-colors text-lg"
          >
            {isPlaying ? "⏸️" : "▶️"}
          </button>

          {/* 音量控制 */}
          <div className="flex items-center gap-2 group/volume">
            <button
              onClick={toggleMute}
              className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center hover:bg-white/30 transition-colors text-sm"
            >
              {volumeIcon}
            </button>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={isMuted ? 0 : volume}
              onChange={handleVolumeChange}
              className="w-0 group-hover/volume:w-20 transition-all duration-200 h-1 bg-white/30 rounded-lg appearance-none cursor-pointer accent-emerald-500"
              style={{ width: '80px' }}
            />
          </div>

          {/* 全屏 */}
          <button
            onClick={handleFullscreen}
            className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center hover:bg-white/30 transition-colors text-lg"
          >
            ⛶
          </button>

          <div className="flex-1" />
          
          {/* LIVE 指示器 */}
          {isPlaying && (
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
              <span className="text-white text-xs font-medium">LIVE</span>
            </div>
          )}
        </div>
      </div>

      {/* 点击视频区域切换播放 */}
      <div 
        className="absolute inset-0 cursor-pointer z-0"
        onClick={handlePlayPause}
      />
    </div>
  );
}
