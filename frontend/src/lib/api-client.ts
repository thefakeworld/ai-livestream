/**
 * API Client with Error Logging
 * Provides typed API calls with automatic error handling and logging
 */

import { logger, loggedFetch } from './logger';

// API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types
export interface ApiResponse<T> {
  data: T | null;
  error: string | null;
  status: number;
}

export interface StreamStatus {
  status: 'idle' | 'starting' | 'running' | 'stopping' | 'error';
  start_time: string | null;
  duration: number;
  bitrate: string;
  error_message: string | null;
  current_content: string | null;
}

export interface DirectorStatus {
  state: 'idle' | 'running' | 'paused' | 'error';
  current_content: string | null;
  uptime: number;
  content_switched: number;
}

export interface Platform {
  platform_type: string;
  display_name: string;
  enabled: boolean;
  configured: boolean;
  status: string;
  rtmp_url: string;
  has_stream_key: boolean;
}

export interface NewsItem {
  title: string;
  content: string;
  source: string;
  url: string;
  published: string | null;
  hash: string;
}

export interface MusicTrack {
  path: string;
  title: string;
  duration: number;
  artist: string;
  size_mb: number;
}

/**
 * API Client Class
 */
class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const startTime = Date.now();

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      const duration = Date.now() - startTime;

      if (!response.ok) {
        const errorText = await response.text().catch(() => 'Unknown error');
        logger.apiError(endpoint, response.status, errorText);
        
        return {
          data: null,
          error: errorText,
          status: response.status,
        };
      }

      const data = await response.json();
      logger.debug(`API Success: ${endpoint}`, { duration: `${duration}ms` });

      return {
        data,
        error: null,
        status: response.status,
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      logger.apiError(endpoint, 0, message, error instanceof Error ? error : undefined);

      return {
        data: null,
        error: message,
        status: 0,
      };
    }
  }

  // Health endpoints
  async getHealth(): Promise<ApiResponse<{ status: string }>> {
    return this.request('/health');
  }

  // Stream endpoints
  async getStreamStatus(): Promise<ApiResponse<StreamStatus>> {
    return this.request('/api/v1/stream/status');
  }

  async startStream(
    videoSource?: string,
    audioSource?: string
  ): Promise<ApiResponse<{ success: boolean; message: string }>> {
    return this.request('/api/v1/stream/start', {
      method: 'POST',
      body: JSON.stringify({ video_source: videoSource, audio_source: audioSource }),
    });
  }

  async stopStream(): Promise<ApiResponse<{ success: boolean; message: string }>> {
    return this.request('/api/v1/stream/stop', {
      method: 'POST',
    });
  }

  async restartStream(): Promise<ApiResponse<{ success: boolean; message: string }>> {
    return this.request('/api/v1/stream/restart', {
      method: 'POST',
    });
  }

  // Director endpoints
  async getDirectorStatus(): Promise<ApiResponse<DirectorStatus>> {
    return this.request('/api/v1/director/status');
  }

  async startDirector(): Promise<ApiResponse<{ success: boolean }>> {
    return this.request('/api/v1/director/start', {
      method: 'POST',
    });
  }

  async stopDirector(): Promise<ApiResponse<{ success: boolean }>> {
    return this.request('/api/v1/director/stop', {
      method: 'POST',
    });
  }

  async switchContent(
    contentType: string,
    contentId?: string
  ): Promise<ApiResponse<{ success: boolean }>> {
    return this.request('/api/v1/director/switch', {
      method: 'POST',
      body: JSON.stringify({ content_type: contentType, content_id: contentId }),
    });
  }

  // Platform endpoints
  async getPlatforms(): Promise<ApiResponse<{ platforms: Record<string, Platform> }>> {
    return this.request('/api/v1/platform/list');
  }

  async getPlatform(platformType: string): Promise<ApiResponse<Platform>> {
    return this.request(`/api/v1/platform/${platformType}`);
  }

  async configurePlatform(
    platformType: string,
    config: {
      rtmp_url: string;
      stream_key: string;
      enabled: boolean;
    }
  ): Promise<ApiResponse<Platform>> {
    return this.request(`/api/v1/platform/${platformType}/config`, {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async enablePlatform(platformType: string): Promise<ApiResponse<{ success: boolean }>> {
    return this.request(`/api/v1/platform/${platformType}/enable`, {
      method: 'POST',
    });
  }

  async disablePlatform(platformType: string): Promise<ApiResponse<{ success: boolean }>> {
    return this.request(`/api/v1/platform/${platformType}/disable`, {
      method: 'POST',
    });
  }

  // Content endpoints
  async getNews(): Promise<ApiResponse<NewsItem[]>> {
    return this.request('/api/v1/content/news');
  }

  async getMusic(): Promise<ApiResponse<MusicTrack[]>> {
    return this.request('/api/v1/content/music');
  }

  async getVideos(): Promise<ApiResponse<{ path: string; title: string }[]>> {
    return this.request('/api/v1/content/videos');
  }

  async getPlaylist(): Promise<ApiResponse<{
    items: Array<{
      id: string;
      content_type: string;
      path: string;
      title: string;
      duration: number;
    }>;
    current_index: number;
    total_duration: number;
  }>> {
    return this.request('/api/v1/content/playlist');
  }

  // Logs endpoint (send frontend logs to backend)
  async sendFrontendLog(logEntry: Record<string, unknown>): Promise<void> {
    try {
      await fetch(`${this.baseUrl}/api/v1/logs/frontend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(logEntry),
      });
    } catch {
      // Silently fail
    }
  }
}

// Export singleton instance
export const api = new ApiClient();

// Export class for testing
export { ApiClient };
