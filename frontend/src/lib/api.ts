/**
 * API Client for AI Livestream Backend
 */

// 使用相对路径，通过 Next.js rewrites 代理到后端
const API_BASE = '/api/v1';

interface ApiResponse<T> {
  data?: T;
  error?: string;
}

// Stream API
export const streamApi = {
  getStatus: async () => {
    const res = await fetch(`${API_BASE}/stream/status`);
    return res.json();
  },

  start: async (params: { video_source?: string; audio_source?: string; platforms?: string[] }) => {
    const res = await fetch(`${API_BASE}/stream/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    return res.json();
  },

  stop: async () => {
    const res = await fetch(`${API_BASE}/stream/stop`, { method: 'POST' });
    return res.json();
  },

  restart: async () => {
    const res = await fetch(`${API_BASE}/stream/restart`, { method: 'POST' });
    return res.json();
  },
};

// Director API
export const directorApi = {
  getStatus: async () => {
    const res = await fetch(`${API_BASE}/director/status`);
    return res.json();
  },

  start: async () => {
    const res = await fetch(`${API_BASE}/director/start`, { method: 'POST' });
    return res.json();
  },

  stop: async () => {
    const res = await fetch(`${API_BASE}/director/stop`, { method: 'POST' });
    return res.json();
  },

  switchContent: async (params: { content_type: string; content_id?: string }) => {
    const res = await fetch(`${API_BASE}/director/switch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    return res.json();
  },

  getQueue: async () => {
    const res = await fetch(`${API_BASE}/director/queue`);
    return res.json();
  },
};

// Platform API
export const platformApi = {
  list: async () => {
    const res = await fetch(`${API_BASE}/platform/list`);
    return res.json();
  },

  get: async (platformType: string) => {
    const res = await fetch(`${API_BASE}/platform/${platformType}`);
    return res.json();
  },

  add: async (config: { platform_type: string; rtmp_url: string; stream_key: string; enabled?: boolean }) => {
    const res = await fetch(`${API_BASE}/platform/add`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    return res.json();
  },

  remove: async (platformType: string) => {
    const res = await fetch(`${API_BASE}/platform/${platformType}`, { method: 'DELETE' });
    return res.json();
  },

  enable: async (platformType: string) => {
    const res = await fetch(`${API_BASE}/platform/${platformType}/enable`, { method: 'POST' });
    return res.json();
  },

  disable: async (platformType: string) => {
    const res = await fetch(`${API_BASE}/platform/${platformType}/disable`, { method: 'POST' });
    return res.json();
  },

  updateKey: async (platformType: string, streamKey: string) => {
    const res = await fetch(`${API_BASE}/platform/${platformType}/key?stream_key=${encodeURIComponent(streamKey)}`, {
      method: 'POST',
    });
    return res.json();
  },

  getAvailable: async () => {
    const res = await fetch(`${API_BASE}/platform/available`);
    return res.json();
  },
};

// Content API
export const contentApi = {
  list: async () => {
    const res = await fetch(`${API_BASE}/content/list`);
    return res.json();
  },

  getNews: async () => {
    const res = await fetch(`${API_BASE}/content/news`);
    return res.json();
  },

  refreshNews: async () => {
    const res = await fetch(`${API_BASE}/content/news/refresh`, { method: 'POST' });
    return res.json();
  },

  getMusic: async () => {
    const res = await fetch(`${API_BASE}/content/music`);
    return res.json();
  },

  downloadMusic: async (query: string) => {
    const res = await fetch(`${API_BASE}/content/music/download?query=${encodeURIComponent(query)}`, {
      method: 'POST',
    });
    return res.json();
  },

  getVideos: async () => {
    const res = await fetch(`${API_BASE}/content/videos`);
    return res.json();
  },

  getAll: async () => {
    const res = await fetch(`${API_BASE}/content/all`);
    return res.json();
  },
};

// Danmaku API
export const danmakuApi = {
  getHistory: async (limit: number = 50, platform?: string) => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (platform) params.append('platform', platform);
    const res = await fetch(`${API_BASE}/danmaku/history?${params}`);
    return res.json();
  },

  getStats: async () => {
    const res = await fetch(`${API_BASE}/danmaku/stats`);
    return res.json();
  },

  send: async (platform: string, message: string) => {
    const res = await fetch(`${API_BASE}/danmaku/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ platform, message }),
    });
    return res.json();
  },
};

// AI Agent API
export const aiApi = {
  analyze: async (messages: Array<{id: string; user: string; content: string; platform: string; timestamp: number}>) => {
    const res = await fetch(`${API_BASE}/ai/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(messages),
    });
    return res.json();
  },

  respond: async (message: string, context?: Record<string, unknown>) => {
    const res = await fetch(`${API_BASE}/ai/respond`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, context }),
    });
    return res.json();
  },

  getSuggestions: async () => {
    const res = await fetch(`${API_BASE}/ai/suggestions`);
    return res.json();
  },

  acceptSuggestion: async (suggestionId: string) => {
    const res = await fetch(`${API_BASE}/ai/suggestions/${suggestionId}/accept`, { method: 'POST' });
    return res.json();
  },

  dismissSuggestion: async (suggestionId: string) => {
    const res = await fetch(`${API_BASE}/ai/suggestions/${suggestionId}/dismiss`, { method: 'POST' });
    return res.json();
  },
};

// Layer API
export const layerApi = {
  list: async () => {
    const res = await fetch(`${API_BASE}/layers`);
    return res.json();
  },

  get: async (layerId: string) => {
    const res = await fetch(`${API_BASE}/layers/${layerId}`);
    return res.json();
  },

  add: async (layer: {
    id: string;
    type: 'video' | 'image' | 'text' | 'audio';
    name: string;
    source: string;
    visible?: boolean;
    order?: number;
    options?: Record<string, unknown>;
  }) => {
    const res = await fetch(`${API_BASE}/layers/add`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(layer),
    });
    return res.json();
  },

  update: async (layerId: string, updates: {
    visible?: boolean;
    order?: number;
    options?: Record<string, unknown>;
  }) => {
    const res = await fetch(`${API_BASE}/layers/update/${layerId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
    return res.json();
  },

  remove: async (layerId: string) => {
    const res = await fetch(`${API_BASE}/layers/${layerId}`, { method: 'DELETE' });
    return res.json();
  },

  reorder: async (layerIds: string[]) => {
    const res = await fetch(`${API_BASE}/layers/reorder`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(layerIds),
    });
    return res.json();
  },

  clear: async () => {
    const res = await fetch(`${API_BASE}/layers/clear`, { method: 'POST' });
    return res.json();
  },

  getTemplates: async () => {
    const res = await fetch(`${API_BASE}/layers/templates/list`);
    return res.json();
  },

  applyTemplate: async (templateName: string, source: string, layerId?: string) => {
    const params = new URLSearchParams({ source });
    if (layerId) params.append('layer_id', layerId);
    const res = await fetch(`${API_BASE}/layers/templates/apply/${templateName}?${params}`, {
      method: 'POST',
    });
    return res.json();
  },

  startComposition: async (outputPath?: string, duration?: number, format?: string) => {
    const params = new URLSearchParams();
    if (outputPath) params.append('output_path', outputPath);
    if (duration) params.append('duration', String(duration));
    if (format) params.append('output_format', format);
    const res = await fetch(`${API_BASE}/layers/composition/start?${params}`, { method: 'POST' });
    return res.json();
  },

  stopComposition: async () => {
    const res = await fetch(`${API_BASE}/layers/composition/stop`, { method: 'POST' });
    return res.json();
  },

  getCompositionStatus: async () => {
    const res = await fetch(`${API_BASE}/layers/composition/status`);
    return res.json();
  },
};
