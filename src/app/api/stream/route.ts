import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";
import fs from "fs";
import path from "path";

const execAsync = promisify(exec);

const RTMP_URL = "rtmp://a.rtmp.youtube.com/live2";
const STREAM_KEY = "hdb0-bxcg-ua45-hg30-78r0";
const PROJECT_PATH = "/home/z/my-project/download/digital-human-livestream";

interface StreamStatus {
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
  youtubeConnected: boolean;
  streamHealth: "healthy" | "warning" | "error";
  lastError: string;
  restartCount: number;
}

async function checkYouTubeConnection(): Promise<boolean> {
  try {
    const { stdout } = await execAsync(
      "timeout 5 bash -c 'echo > /dev/tcp/a.rtmp.youtube.com/1935' 2>&1",
      { timeout: 10000 }
    );
    return true;
  } catch {
    return false;
  }
}

async function getFfmpegStatus(): Promise<StreamStatus> {
  const defaultStatus: StreamStatus = {
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
    youtubeConnected: false,
    streamHealth: "error",
    lastError: "",
    restartCount: 0
  };

  try {
    // Check FFmpeg process
    const { stdout: pidOutput } = await execAsync(
      "pgrep -f 'ffmpeg.*(concat|rtmp|youtube)'",
      { timeout: 5000 }
    ).catch(() => ({ stdout: "" }));

    const pids = pidOutput.trim().split('\n').filter(p => p.trim());
    const pid = pids.length > 0 ? parseInt(pids[0]) : null;
    
    // Check YouTube connection
    const youtubeConnected = await checkYouTubeConnection();
    
    if (!pid) {
      return {
        ...defaultStatus,
        youtubeConnected,
        streamHealth: youtubeConnected ? "warning" : "error",
        lastError: "推流进程未运行"
      };
    }

    // Get process command to check playlist mode
    const { stdout: cmdOutput } = await execAsync(
      `ps -p ${pid} -o args= --no-headers`,
      { timeout: 5000 }
    ).catch(() => ({ stdout: "" }));
    
    const isPlaylistMode = cmdOutput.includes('concat') || cmdOutput.includes('playlist');

    // Get uptime
    let uptime = "--:--:--";
    try {
      const { stdout: uptimeOut } = await execAsync(
        `ps -p ${pid} -o etime= --no-headers`,
        { timeout: 5000 }
      );
      uptime = uptimeOut.trim() || "--:--:--";
    } catch {
      // ignore
    }

    // Get CPU/memory
    let cpuUsage = "";
    let memoryUsage = "";
    try {
      const { stdout: resourceOut } = await execAsync(
        `ps -p ${pid} -o %cpu,%mem --no-headers`,
        { timeout: 5000 }
      );
      const parts = resourceOut.trim().split(/\s+/);
      cpuUsage = parts[0] || "";
      memoryUsage = parts[1] || "";
    } catch {
      // ignore
    }

    // Check video file
    const videoFile = path.join(PROJECT_PATH, "output", "news_broadcast.mp4");
    let videoPath = "";
    let videoSize = "";
    if (fs.existsSync(videoFile)) {
      videoPath = videoFile;
      const stats = fs.statSync(videoFile);
      videoSize = `${(stats.size / 1024 / 1024).toFixed(1)} MB`;
    }

    // Count news files
    const newsCache = path.join(PROJECT_PATH, "assets", "news", "news_cache.json");
    let newsCount = 0;
    if (fs.existsSync(newsCache)) {
      try {
        const content = fs.readFileSync(newsCache, "utf-8");
        const news = JSON.parse(content);
        newsCount = Array.isArray(news) ? news.length : 0;
      } catch {
        // ignore
      }
    }

    // Count music files
    const musicDir = path.join(PROJECT_PATH, "music");
    let musicCount = 0;
    if (fs.existsSync(musicDir)) {
      try {
        const files = fs.readdirSync(musicDir).filter(f => f.endsWith('.mp3'));
        musicCount = files.length;
      } catch {
        // ignore
      }
    }

    // Calculate playlist duration
    const avgSongDuration = 4;
    const newsDuration = 5.5;
    const totalMinutes = (newsDuration * 5) + (musicCount * avgSongDuration * 0.5);
    const hours = Math.floor(totalMinutes / 60);
    const mins = Math.floor(totalMinutes % 60);
    const totalPlaylistDuration = hours > 0 
      ? `~${hours}h ${mins}m`
      : `~${mins}m`;

    // Check monitor log for restart count
    let restartCount = 0;
    let lastError = "";
    const logFile = path.join(PROJECT_PATH, "logs", "stream_monitor.log");
    if (fs.existsSync(logFile)) {
      try {
        const logContent = fs.readFileSync(logFile, "utf-8");
        const restartMatches = logContent.match(/重启推流/g);
        restartCount = restartMatches ? restartMatches.length : 0;
        
        // Get last error from log
        const errorMatch = logContent.match(/(?:失败|错误|异常|退出)[^\n]*/g);
        if (errorMatch && errorMatch.length > 0) {
          lastError = errorMatch[errorMatch.length - 1];
        }
      } catch {
        // ignore
      }
    }

    // Determine stream health
    let streamHealth: "healthy" | "warning" | "error" = "healthy";
    if (!youtubeConnected) {
      streamHealth = "error";
    } else if (parseFloat(cpuUsage) > 80 || parseFloat(memoryUsage) > 50) {
      streamHealth = "warning";
    }

    return {
      isStreaming: true,
      ffmpegPid: pid,
      uptime,
      cpuUsage,
      memoryUsage,
      videoPath,
      videoSize,
      newsCount,
      musicCount,
      playlistMode: isPlaylistMode,
      totalPlaylistDuration,
      youtubeConnected,
      streamHealth,
      lastError,
      restartCount
    };
  } catch (error) {
    return {
      ...defaultStatus,
      lastError: error instanceof Error ? error.message : "Unknown error"
    };
  }
}

export async function GET() {
  try {
    const status = await getFfmpegStatus();
    
    return NextResponse.json({
      success: true,
      ...status,
      rtmpUrl: RTMP_URL,
      streamKey: STREAM_KEY.slice(0, 8) + "...",
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : "Unknown error"
    }, { status: 500 });
  }
}
