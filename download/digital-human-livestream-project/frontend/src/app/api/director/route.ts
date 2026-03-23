import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";
import fs from "fs";
import path from "path";

const execAsync = promisify(exec);

const PROJECT_PATH = "/home/z/my-project/download/digital-human-livestream";
const STATE_FILE = path.join(PROJECT_PATH, "logs", "director_state.json");
const DIRECTOR_SCRIPT = path.join(PROJECT_PATH, "intelligent_director.py");

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

async function runDirectorCommand(cmd: string, data?: any): Promise<any> {
  try {
    const dataArg = data ? `'${JSON.stringify(data)}'` : "";
    const { stdout } = await execAsync(
      `cd ${PROJECT_PATH} && python3 intelligent_director.py ${cmd} ${dataArg} 2>/dev/null`,
      { timeout: 10000 }
    );
    
    // Find JSON start - look for line that starts with { or [
    // But skip log lines that look like [2024-...]
    const lines = stdout.split('\n');
    let jsonStartIndex = -1;
    
    for (let i = 0; i < lines.length; i++) {
      const trimmed = lines[i].trim();
      // Check if it's a JSON object or array (not a log line like [2024-...)
      if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
        // Make sure it's not a log line (log lines start with [YYYY-...)
        if (!trimmed.match(/^\[\d{4}-\d{2}-\d{2}/)) {
          jsonStartIndex = i;
          break;
        }
      }
    }
    
    if (jsonStartIndex === -1) {
      return { success: false, error: "No JSON found in output" };
    }
    
    const jsonOutput = lines.slice(jsonStartIndex).join('\n');
    return JSON.parse(jsonOutput);
  } catch (error) {
    return { success: false, error: String(error) };
  }
}

async function getNetworkStatus(): Promise<string> {
  try {
    const { stdout } = await execAsync(
      "ss -tnp 2>/dev/null | grep '1935' | grep ffmpeg || echo ''",
      { timeout: 3000 }
    );
    
    if (stdout.includes("ESTAB")) return "connected";
    if (stdout.includes("CLOSE-WAIT")) return "closing";
    if (stdout.includes("SYN-SENT")) return "connecting";
    if (stdout.trim()) return "unknown";
    return "disconnected";
  } catch {
    return "unknown";
  }
}

async function getFFmpegProgress(): Promise<{ fps: number; bitrate: string; time: string }> {
  try {
    const logFile = path.join(PROJECT_PATH, "logs", "ffmpeg_realtime.log");
    if (!fs.existsSync(logFile)) {
      return { fps: 30, bitrate: "2500 kbps", time: "00:00:00" };
    }
    
    const { stdout } = await execAsync(`tail -50 "${logFile}" | grep "frame=" | tail -1`, { timeout: 3000 });
    
    const fpsMatch = stdout.match(/fps=\s*([\d.]+)/);
    const bitrateMatch = stdout.match(/bitrate=\s*([\d.]+kbits\/s)/);
    const timeMatch = stdout.match(/time=\s*(\d+:\d+:\d+)/);
    
    return {
      fps: fpsMatch ? parseFloat(fpsMatch[1]) : 30,
      bitrate: bitrateMatch ? bitrateMatch[1].replace("kbits/s", " kbps") : "2500 kbps",
      time: timeMatch ? timeMatch[1] : "00:00:00"
    };
  } catch {
    return { fps: 30, bitrate: "2500 kbps", time: "00:00:00" };
  }
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const action = searchParams.get("action") || "status";

  try {
    if (action === "list") {
      const result = await runDirectorCommand("list");
      return NextResponse.json(result);
    }
    
    if (action === "playlist") {
      const mode = searchParams.get("mode") || "mixed";
      const result = await runDirectorCommand("playlist", { mode });
      return NextResponse.json(result);
    }
    
    if (action === "platforms") {
      const result = await runDirectorCommand("platforms");
      return NextResponse.json(result);
    }
    
    const directorResult = await runDirectorCommand("status");
    const networkStatus = await getNetworkStatus();
    const ffmpegProgress = await getFFmpegProgress();
    
    let contentProgress = 0;
    let remainingTime = 0;
    if (directorResult.data?.current_content) {
      const content = directorResult.data.current_content;
      if (content.duration > 0 && content.position > 0) {
        contentProgress = (content.position / content.duration) * 100;
        remainingTime = Math.max(0, content.duration - content.position);
      }
    }
    
    return NextResponse.json({
      success: true,
      ...directorResult.data,
      networkStatus,
      ffmpegProgress,
      contentProgress,
      remainingTime,
      timestamp: new Date().toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" })
    });
    
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : "Unknown error"
    }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, data } = body;
    
    let result;
    
    switch (action) {
      case "start":
        result = await runDirectorCommand("start", data);
        break;
      case "stop":
        result = await runDirectorCommand("stop");
        break;
      case "next":
        result = await runDirectorCommand("next");
        break;
      case "switch":
        result = await runDirectorCommand("switch", data);
        break;
      case "mode":
        result = { success: true, message: `模式已切换到 ${data?.mode || "auto"}` };
        break;
      // 多平台管理
      case "enable_platform":
        result = await runDirectorCommand("enable_platform", data);
        break;
      case "disable_platform":
        result = await runDirectorCommand("disable_platform", data);
        break;
      case "set_stream_key":
        result = await runDirectorCommand("set_stream_key", data);
        break;
      default:
        result = { success: false, error: `未知操作: ${action}` };
    }
    
    return NextResponse.json(result);
    
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : "Unknown error"
    }, { status: 500 });
  }
}
