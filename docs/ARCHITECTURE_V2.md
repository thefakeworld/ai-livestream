# AI 直播导播台 V2 架构设计

## 一、需求分析

### 核心功能
1. **多流叠加播放**：主视频 + 图片层 + 文字层 + 语音播报
2. **弹幕互动系统**：实时显示弹幕，AI 智能识别并响应
3. **智能控制**：根据弹幕内容自动/手动切换内容、回复互动

### 三栏布局
```
┌──────────────┬──────────────────────────┬────────────────┐
│              │                          │                │
│   控制面板    │      视频预览区           │    弹幕互动    │
│   (左侧栏)    │      (中间主区域)         │    (右侧栏)    │
│              │                          │                │
│  • 内容选择   │  ┌──────────────────┐   │  • 实时弹幕    │
│  • 图层管理   │  │                  │   │  • AI 建议回复 │
│  • 平台状态   │  │  主视频 + 叠加层  │   │  • 快捷操作    │
│  • 播放控制   │  │                  │   │  • 互动统计    │
│              │  └──────────────────┘   │                │
│              │                          │                │
└──────────────┴──────────────────────────┴────────────────┘
```

---

## 二、架构设计

### 2.1 整体架构图

```
                    ┌─────────────────────────────────────────┐
                    │            Frontend (Next.js)           │
                    │  ┌─────────┬─────────────┬────────────┐ │
                    │  │Control  │   Preview   │  Chat/     │ │
                    │  │Panel    │   Player    │  Danmaku   │ │
                    │  └────┬────┴──────┬──────┴─────┬──────┘ │
                    └───────┼───────────┼────────────┼────────┘
                            │           │            │
                            ▼           ▼            ▼
                    ┌─────────────────────────────────────────┐
                    │            API Gateway (FastAPI)        │
                    └───────────────────┬─────────────────────┘
                                        │
            ┌───────────────────────────┼───────────────────────────┐
            │                           │                           │
            ▼                           ▼                           ▼
    ┌───────────────┐          ┌───────────────┐          ┌───────────────┐
    │ Layer Manager │          │  Danmaku      │          │  AI Agent     │
    │ Service       │          │  Service      │          │  Service      │
    │               │          │               │          │               │
    │ • 图层合成    │          │ • 弹幕收集    │          │ • 意图识别    │
    │ • 流切换      │          │ • 平台聚合    │          │ • 自动回复    │
    │ • 效果叠加    │          │ • 过滤审核    │          │ • 内容推荐    │
    └───────┬───────┘          └───────┬───────┘          └───────┬───────┘
            │                          │                          │
            ▼                          ▼                          ▼
    ┌───────────────┐          ┌───────────────┐          ┌───────────────┐
    │ FFmpeg        │          │ Platform      │          │ LLM API       │
    │ Compositor    │          │ Adapters      │          │ (z-ai-sdk)    │
    └───────────────┘          └───────────────┘          └───────────────┘
```

### 2.2 服务拆分

| 服务 | 职责 | 接口 |
|------|------|------|
| **LayerManager** | 管理视频层、图片层、文字层的叠加 | `POST /layers/add`, `/layers/remove`, `/layers/reorder` |
| **DanmakuService** | 收集、过滤、展示弹幕 | `WS /ws/danmaku`, `GET /danmaku/history` |
| **AIAgentService** | 分析弹幕意图，生成回复和动作建议 | `POST /ai/analyze`, `POST /ai/respond` |
| **StreamCompositor** | FFmpeg 实现的多流合成 | 内部服务，通过队列通信 |

---

## 三、数据流设计

### 3.1 视频流合成流程

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ 视频源   │    │ 图片层   │    │ 文字层   │    │ 音频层   │
│ (主)    │    │ (背景)   │    │ (字幕)   │    │ (TTS)   │
└────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘
     │              │              │              │
     └──────────────┴──────────────┴──────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Layer Compositor │
                  │  (FFmpeg filter) │
                  │                 │
                  │  overlay=       │
                  │  drawtext=      │
                  │  amix=          │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │   HLS Output    │
                  │   (预览/推流)    │
                  └─────────────────┘
```

### 3.2 弹幕处理流程

```
平台弹幕 ──┬── YouTube Live Chat API
           ├── B站 弹幕 API
           ├── TikTok Live
           └── 抖音 直播
                    │
                    ▼
           ┌──────────────┐
           │  Danmaku     │
           │  Aggregator  │──→ 过滤敏感词
           │              │──→ 去重
           └──────┬───────┘
                  │
                  ├─────────────────────┐
                  │                     │
                  ▼                     ▼
           ┌──────────────┐      ┌──────────────┐
           │  WebSocket   │      │  AI Agent    │
           │  → Frontend  │      │  Analysis    │
           └──────────────┘      └──────┬───────┐
                                        │       │
                                        ▼       ▼
                                  ┌─────────┐ ┌─────────┐
                                  │ 意图识别 │ │ 自动回复 │
                                  │ 切歌/切 │ │ 打招呼  │
                                  │ 换视频  │ │ 回答问题│
                                  └─────────┘ └─────────┘
```

### 3.3 AI 响应类型

```typescript
interface AIResponse {
  type: 'switch_content' | 'reply' | 'greeting' | 'action';
  confidence: number;  // 置信度 0-1
  action?: {
    type: 'switch_music' | 'switch_video' | 'add_overlay';
    target: string;
  };
  reply?: {
    text: string;
    tts: boolean;  // 是否语音播报
  };
}
```

---

## 四、前端组件结构

### 4.1 组件树

```
DirectorPage (page.tsx)
├── Layout (三栏布局容器)
│   ├── LeftPanel (控制面板)
│   │   ├── ContentSelector (内容选择)
│   │   ├── LayerManager (图层管理)
│   │   │   ├── VideoLayer
│   │   │   ├── ImageLayer
│   │   │   └── TextLayer
│   │   ├── PlatformStatus (平台状态)
│   │   └── PlaybackControls (播放控制)
│   │
│   ├── CenterPanel (视频预览)
│   │   ├── HLSPlayer (视频播放器)
│   │   ├── LayerOverlay (图层叠加显示)
│   │   └── StatusBar (状态栏)
│   │
│   └── RightPanel (弹幕互动)
│       ├── DanmakuFeed (弹幕流)
│       ├── AISuggestions (AI 建议)
│       ├── QuickActions (快捷操作)
│       └── InteractionStats (互动统计)
│
└── Modals
    ├── ContentLibraryModal
    ├── SettingsModal
    └── AIMonitorModal
```

### 4.2 状态管理

```typescript
// 全局状态 (可选用 Zustand 或 Context)
interface DirectorState {
  // 播放状态
  playback: {
    isPlaying: boolean;
    currentContent: ContentItem | null;
    uptime: number;
  };
  
  // 图层管理
  layers: {
    video: VideoLayer | null;
    images: ImageLayer[];
    texts: TextLayer[];
    audio: AudioLayer | null;
  };
  
  // 弹幕数据
  danmaku: {
    messages: DanmakuMessage[];
    unreadCount: number;
  };
  
  // AI 状态
  ai: {
    suggestions: AISuggestion[];
    autoMode: boolean;  // AI 自动模式
  };
}
```

---

## 五、API 接口设计

### 5.1 图层管理 API

```yaml
# 图层操作
POST /api/v1/layers/add
  body: { type: 'video'|'image'|'text'|'audio', source: string, options: LayerOptions }
  
POST /api/v1/layers/remove
  body: { layerId: string }
  
POST /api/v1/layers/reorder
  body: { layerIds: string[] }

POST /api/v1/layers/visibility
  body: { layerId: string, visible: boolean }

# 获取当前图层状态
GET /api/v1/layers
  response: { layers: Layer[] }
```

### 5.2 弹幕 API

```yaml
# WebSocket 连接
WS /api/v1/ws/danmaku
  message: { type: 'danmaku', data: DanmakuMessage }
  
# 弹幕历史
GET /api/v1/danmaku/history
  query: { limit: number, platform?: string }
  
# 发送弹幕/回复
POST /api/v1/danmaku/send
  body: { platform: string, message: string }
```

### 5.3 AI Agent API

```yaml
# 分析弹幕意图
POST /api/v1/ai/analyze
  body: { messages: DanmakuMessage[] }
  response: { intents: Intent[] }
  
# 生成回复
POST /api/v1/ai/respond
  body: { message: string, context: Context }
  response: { reply: string, action?: Action }
  
# AI 建议流 (WebSocket)
WS /api/v1/ws/ai-suggestions
  message: { type: 'suggestion', data: AISuggestion }
```

---

## 六、可测试性设计

### 6.1 单元测试

```python
# 后端测试结构
tests/
├── unit/
│   ├── test_layer_manager.py    # 图层管理逻辑
│   ├── test_danmaku_filter.py   # 弹幕过滤
│   └── test_ai_intent.py        # AI 意图识别
├── integration/
│   ├── test_compositor.py       # FFmpeg 合成
│   └── test_platform_adapter.py # 平台适配
└── e2e/
    └── test_director_flow.py    # 完整流程
```

### 6.2 Mock 数据

```typescript
// 前端 Mock
// __mocks__/danmaku.ts
export const mockDanmakuMessages: DanmakuMessage[] = [
  { id: '1', user: '用户A', content: '放首周杰伦的歌', platform: 'bilibili' },
  { id: '2', user: '用户B', content: '主播好', platform: 'douyin' },
  { id: '3', user: '用户C', content: '切下一个视频', platform: 'youtube' },
];

// __mocks__/ai.ts
export const mockAIResponses: AIResponse[] = [
  { type: 'switch_content', action: { type: 'switch_music', target: '周杰伦' }, confidence: 0.92 },
  { type: 'greeting', reply: { text: '欢迎用户B！', tts: true }, confidence: 0.88 },
];
```

### 6.3 测试命令

```bash
# 后端测试
pytest backend/tests/ -v

# 前端测试
npm test -- --coverage

# E2E 测试
playwright test e2e/director.spec.ts
```

---

## 七、维护性设计

### 7.1 模块化

- **每个服务独立目录**，包含：接口、实现、测试
- **接口抽象**：平台适配器、AI 服务都有统一接口
- **依赖注入**：便于替换实现

### 7.2 配置管理

```yaml
# config.yaml
director:
  layers:
    max_count: 10
    video_formats: [mp4, mkv, hls]
  
danmaku:
  filter:
    enabled: true
    sensitive_words: [列表]
  
ai:
  provider: z-ai-sdk
  model: gpt-4
  auto_mode: false
  confidence_threshold: 0.8
```

### 7.3 日志规范

```python
# 统一日志格式
{
  "timestamp": "2024-01-15T10:30:00Z",
  "service": "danmaku",
  "level": "INFO",
  "action": "message_received",
  "data": { "platform": "bilibili", "user": "xxx" }
}
```

---

## 八、实施计划

### Phase 1: 基础架构 (1-2天)
- [ ] 重构前端三栏布局
- [ ] 实现图层管理后端
- [ ] 创建 API 接口

### Phase 2: 弹幕系统 (1-2天)
- [ ] 实现 WebSocket 弹幕推送
- [ ] 创建弹幕前端组件
- [ ] 添加 Mock 数据测试

### Phase 3: AI 集成 (2-3天)
- [ ] 接入 z-ai-sdk LLM
- [ ] 实现意图识别
- [ ] 实现自动回复

### Phase 4: 测试优化 (1天)
- [ ] 添加单元测试
- [ ] 添加 E2E 测试
- [ ] 性能优化

---

## 九、技术选型

| 模块 | 技术 | 理由 |
|------|------|------|
| 前端框架 | Next.js 15 + React 18 | 已有基础，SSR 支持 |
| 状态管理 | Zustand | 轻量，易测试 |
| 视频播放 | HLS.js | 成熟稳定 |
| WebSocket | FastAPI WebSocket | 原生支持 |
| AI 服务 | z-ai-sdk | 已集成 |
| 流合成 | FFmpeg | 行业标准 |

---

## 十、风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| FFmpeg 合成性能 | 高 | 使用 GPU 加速，降低分辨率预览 |
| 弹幕量过大 | 中 | 消息队列削峰，前端虚拟滚动 |
| AI 响应延迟 | 中 | 异步处理，缓存常见回复 |
| 平台 API 变化 | 中 | 抽象适配层，快速迭代 |

