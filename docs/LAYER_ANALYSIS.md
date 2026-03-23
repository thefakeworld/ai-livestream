# 图层管理功能分析报告

## 一、设计目标

### 1.1 核心功能
根据 `ARCHITECTURE_V2.md` 设计，图层管理应实现：

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ 视频源   │    │ 图片层   │    │ 文字层   │    │ 音频层   │
│ (主)    │    │ (背景)   │    │ (字幕)   │    │ (TTS)   │
└────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘
     └──────────────┴──────────────┴──────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  FFmpeg filter  │
                  │  - overlay=     │  图片叠加
                  │  - drawtext=    │  文字叠加
                  │  - amix=        │  音频混合
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │   HLS/RTMP      │
                  │   输出           │
                  └─────────────────┘
```

### 1.2 图层属性
| 属性 | 说明 | FFmpeg 参数 |
|------|------|-------------|
| position | 位置 (x, y) | overlay=x:y |
| size | 大小 (w, h) | scale=w:h |
| opacity | 透明度 0-1 | format=rgba, colorchannelmixer |
| order | 层级顺序 | filter_complex 链顺序 |

---

## 二、当前实现情况

### 2.1 ✅ 已完成

| 模块 | 文件 | 功能 | 状态 |
|------|------|------|------|
| 前端组件 | `LayerManager.tsx` | 图层列表 UI | ✅ |
| 图层数据结构 | `LayerManager.tsx` | Layer 接口定义 | ✅ |
| 拖拽排序 | `LayerManager.tsx` | handleDragStart/Over/End | ✅ |
| 显隐控制 | `LayerManager.tsx` | onToggleVisibility | ✅ |
| 添加/删除 | `director/page.tsx` | handleAddLayer/handleRemoveLayer | ✅ |
| 图层类型 | `LayerManager.tsx` | video/image/text/audio | ✅ |

### 2.2 ⚠️ 部分完成

| 功能 | 当前状态 | 缺失部分 |
|------|----------|----------|
| 透明度调节 | UI 显示但 `readOnly` | 需要添加 onChange 和后端支持 |
| 图层预览 | 只有主视频播放器 | 需要叠加层预览组件 |

### 2.3 ❌ 未实现

| 功能 | 设计要求 | 当前状态 |
|------|----------|----------|
| FFmpeg 多层合成 | filter_complex | 未实现，当前只支持单视频源 |
| 后端图层 API | `/api/v1/layers/*` | 未实现 |
| 图层位置调整 | 拖拽调整 x,y | 未实现 |
| 图层大小调整 | scale 参数 | 未实现 |
| 文字层参数 | 字体、颜色、大小 | 未实现 |
| 音频混合 | amix 滤镜 | 未实现 |

---

## 三、代码差距分析

### 3.1 前端 LayerManager 组件

**当前实现**:
```typescript
// 图层类型定义 - ✅ 完整
export interface Layer {
  id: string;
  type: "video" | "image" | "text" | "audio";
  name: string;
  source: string;
  visible: boolean;
  order: number;
  options?: {
    position?: { x: number; y: number };  // ✅ 定义了
    size?: { width: number; height: number };  // ✅ 定义了
    opacity?: number;  // ✅ 定义了
  };
}

// 透明度滑块 - ⚠️ readOnly，无实际功能
<input
  type="range"
  value={(layer.options?.opacity ?? 1) * 100}
  className="flex-1 h-1 accent-emerald-500"
  readOnly  // ❌ 应该有 onChange
/>
```

**缺失**:
1. 没有 `onUpdateLayer` 回调来更新图层属性
2. 没有位置/大小调整 UI
3. 文字层没有字体、颜色设置

### 3.2 后端 FFmpegStreamer

**当前实现**:
```python
# ffmpeg_streamer.py - 只支持单一源
def build_command(self) -> List[str]:
    # 只有一个 video_source 和一个 audio_source
    if self.video_source:
        cmd.extend(["-i", self.video_source])
    # ...
```

**缺失**:
1. 没有 layers 列表属性
2. 没有 filter_complex 构建
3. 没有 overlay/drawtext/amix 支持

---

## 四、实现差距与优先级

### 4.1 高优先级 (核心功能)

1. **后端 LayerCompositor 服务**
   - 创建 `backend/streaming/layer_compositor.py`
   - 实现 FFmpeg filter_complex 构建
   - 支持多图层叠加

2. **后端图层 API**
   - `POST /api/v1/layers/add` - 添加图层
   - `POST /api/v1/layers/remove` - 移除图层
   - `POST /api/v1/layers/update` - 更新图层属性
   - `GET /api/v1/layers` - 获取图层层列表

### 4.2 中优先级 (增强功能)

3. **前端图层属性编辑**
   - 透明度滑块功能化
   - 位置调整（数字输入）
   - 大小调整

4. **前端预览叠加**
   - 在 HLSPlayer 上叠加显示图片层
   - 文字层使用 CSS overlay

### 4.3 低优先级 (优化功能)

5. **可视化拖拽定位**
   - 直接在视频区域拖拽图层位置
   - 实时预览

6. **文字层高级设置**
   - 字体选择
   - 颜色选择
   - 动画效果

---

## 五、建议实现步骤

### Step 1: 后端图层服务 (1天)

```python
# backend/streaming/layer_compositor.py
class LayerCompositor:
    def __init__(self):
        self.layers: List[Layer] = []
    
    def add_layer(self, layer: Layer): ...
    def remove_layer(self, layer_id: str): ...
    def update_layer(self, layer_id: str, options: dict): ...
    
    def build_filter_complex(self) -> str:
        """构建 FFmpeg filter_complex 字符串"""
        # overlay 逻辑
        # drawtext 逻辑
        # amix 逻辑
```

### Step 2: 图层 API 路由 (0.5天)

```python
# backend/api/routes/layers.py
@router.post("/add")
async def add_layer(layer: LayerRequest): ...

@router.post("/remove") 
async def remove_layer(layer_id: str): ...

@router.get("/")
async def list_layers(): ...
```

### Step 3: 前端属性编辑 (0.5天)

```typescript
// LayerManager.tsx
interface LayerManagerProps {
  // 添加
  onUpdateLayer: (layerId: string, options: LayerOptions) => void;
}

// 透明度滑块
<input
  onChange={(e) => onUpdateLayer(layer.id, { opacity: e.target.value })}
/>
```

### Step 4: 前端预览叠加 (1天)

```typescript
// PreviewOverlay.tsx - 叠加层预览组件
<div className="relative">
  <HLSPlayer src={mainVideo} />
  {imageLayers.map(layer => (
    <img 
      src={layer.source}
      style={{ 
        position: 'absolute',
        left: layer.options.position.x,
        top: layer.options.position.y,
        opacity: layer.options.opacity
      }}
    />
  ))}
  {textLayers.map(layer => (
    <div style={{
      position: 'absolute',
      left: layer.options.position.x,
      top: layer.options.position.y,
    }}>
      {layer.content}
    </div>
  ))}
</div>
```

---

## 六、FFmpeg filter_complex 示例

```bash
# 3层叠加示例: 视频 + 图片Logo + 文字字幕
ffmpeg \
  -i main_video.mp4 \           # 输入0: 主视频
  -i logo.png \                  # 输入1: 图片
  -i background_music.mp3 \      # 输入2: 音频
  -filter_complex "\
    [0:v]scale=1920:1080[base]; \
    [1:v]scale=200:100[logo]; \
    [base][logo]overlay=1700:20[video_with_logo]; \
    [video_with_logo]drawtext=text='直播字幕':fontsize=48:fontcolor=white:x=50:y=1000[outv]; \
    [0:a][2:a]amix=inputs=2[aout]" \
  -map "[outv]" -map "[aout]" \
  output.m3u8
```

---

## 七、结论

| 维度 | 设计完成度 | 实现完成度 | 差距 |
|------|-----------|-----------|------|
| 前端 UI | 100% | 60% | 属性编辑、预览叠加 |
| 后端服务 | 100% | 0% | 需要完整实现 |
| FFmpeg 合成 | 100% | 0% | 需要完整实现 |

**总体评估**: 图层管理功能目前完成了前端 UI 骨架，但核心的多层合成功能（后端）完全未实现。这是一个需要重点开发的功能模块。
