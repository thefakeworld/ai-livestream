"use client";

import { useState } from "react";

export interface Layer {
  id: string;
  type: "video" | "image" | "text" | "audio";
  name: string;
  source: string;
  visible: boolean;
  order: number;
  options?: {
    position_x?: number;
    position_y?: number;
    width?: number;
    height?: number;
    opacity?: number;
    font_size?: number;
    font_color?: string;
    volume?: number;
  };
}

interface LayerManagerProps {
  layers: Layer[];
  onToggleVisibility: (layerId: string) => void;
  onReorder: (layerIds: string[]) => void;
  onRemove: (layerId: string) => void;
  onAddLayer: (type: Layer["type"]) => void;
  onUpdateLayer?: (layerId: string, options: Partial<Layer["options"]>) => void;
}

export default function LayerManager({
  layers,
  onToggleVisibility,
  onReorder,
  onRemove,
  onAddLayer,
  onUpdateLayer,
}: LayerManagerProps) {
  const [draggedId, setDraggedId] = useState<string | null>(null);
  const [expandedLayer, setExpandedLayer] = useState<string | null>(null);

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "video": return "🎬";
      case "image": return "🖼️";
      case "text": return "📝";
      case "audio": return "🔊";
      default: return "📄";
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case "video": return "border-orange-500/50";
      case "image": return "border-green-500/50";
      case "text": return "border-blue-500/50";
      case "audio": return "border-purple-500/50";
      default: return "border-gray-500/50";
    }
  };

  const handleDragStart = (id: string) => {
    setDraggedId(id);
  };

  const handleDragOver = (e: React.DragEvent, targetId: string) => {
    e.preventDefault();
    if (!draggedId || draggedId === targetId) return;

    const newLayers = [...layers];
    const draggedIndex = newLayers.findIndex(l => l.id === draggedId);
    const targetIndex = newLayers.findIndex(l => l.id === targetId);

    if (draggedIndex !== -1 && targetIndex !== -1) {
      const [removed] = newLayers.splice(draggedIndex, 1);
      newLayers.splice(targetIndex, 0, removed);
      onReorder(newLayers.map(l => l.id));
    }
  };

  const handleDragEnd = () => {
    setDraggedId(null);
  };

  const handleOpacityChange = (layerId: string, value: number) => {
    if (onUpdateLayer) {
      onUpdateLayer(layerId, { opacity: value / 100 });
    }
  };

  const handlePositionChange = (layerId: string, axis: "x" | "y", value: number) => {
    if (onUpdateLayer) {
      onUpdateLayer(layerId, axis === "x" ? { position_x: value } : { position_y: value });
    }
  };

  const handleSizeChange = (layerId: string, dimension: "width" | "height", value: number) => {
    if (onUpdateLayer) {
      onUpdateLayer(layerId, dimension === "width" ? { width: value } : { height: value });
    }
  };

  const handleVolumeChange = (layerId: string, value: number) => {
    if (onUpdateLayer) {
      onUpdateLayer(layerId, { volume: value / 100 });
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* 标题 */}
      <div className="p-3 border-b border-white/5">
        <h3 className="font-semibold text-sm flex items-center gap-2">
          <span>📑</span> 图层管理
        </h3>
        <p className="text-xs text-gray-500 mt-1">添加图层后启动合成查看效果</p>
      </div>

      {/* 添加图层按钮 */}
      <div className="p-2 border-b border-white/5 flex gap-1">
        {[
          { type: "video" as const, icon: "🎬", label: "视频" },
          { type: "image" as const, icon: "🖼️", label: "图片" },
          { type: "text" as const, icon: "📝", label: "文字" },
          { type: "audio" as const, icon: "🔊", label: "音频" },
        ].map(({ type, icon, label }) => (
          <button
            key={type}
            onClick={() => onAddLayer(type)}
            className="flex-1 py-1.5 text-xs bg-gray-700/50 rounded-lg hover:bg-gray-600/50 flex items-center justify-center gap-1"
          >
            <span>{icon}</span>
            <span className="hidden sm:inline">{label}</span>
          </button>
        ))}
      </div>

      {/* 图层列表 */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {layers.length > 0 ? (
          layers.map((layer) => (
            <div
              key={layer.id}
              draggable
              onDragStart={() => handleDragStart(layer.id)}
              onDragOver={(e) => handleDragOver(e, layer.id)}
              onDragEnd={handleDragEnd}
              className={`rounded-lg border-l-2 ${getTypeColor(layer.type)} ${
                draggedId === layer.id ? "opacity-50" : ""
              } ${!layer.visible ? "opacity-60" : ""} bg-gray-700/30 hover:bg-gray-700/50 transition-all cursor-move`}
            >
              {/* 图层头部 */}
              <div className="p-2 flex items-center gap-2">
                <span className="cursor-grab text-gray-500">⋮⋮</span>
                <span className="text-sm">{getTypeIcon(layer.type)}</span>
                <span className="text-xs flex-1 truncate">{layer.name}</span>
                
                {/* 控制按钮 */}
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => onToggleVisibility(layer.id)}
                    className={`w-6 h-6 rounded flex items-center justify-center text-xs ${
                      layer.visible ? "text-emerald-400 bg-emerald-500/20" : "text-gray-500 bg-gray-600/50"
                    }`}
                    title={layer.visible ? "隐藏图层" : "显示图层"}
                  >
                    {layer.visible ? "👁" : "👁‍🗨"}
                  </button>
                  <button
                    onClick={() => setExpandedLayer(expandedLayer === layer.id ? null : layer.id)}
                    className="w-6 h-6 rounded flex items-center justify-center text-xs bg-blue-500/20 text-blue-400"
                    title="编辑属性"
                  >
                    ⚙️
                  </button>
                  <button
                    onClick={() => onRemove(layer.id)}
                    className="w-6 h-6 rounded flex items-center justify-center text-xs text-red-400 bg-red-500/20 hover:bg-red-500/30"
                    title="删除图层"
                  >
                    ✕
                  </button>
                </div>
              </div>

              {/* 展开的属性编辑面板 */}
              {expandedLayer === layer.id && (
                <div className="px-2 pb-2 pt-0 space-y-2 border-t border-white/5">
                  {/* 透明度 */}
                  {layer.type !== "audio" && (
                    <div className="flex items-center gap-2">
                      <label className="text-xs text-gray-400 w-12">透明度</label>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={(layer.options?.opacity ?? 1) * 100}
                        onChange={(e) => handleOpacityChange(layer.id, parseInt(e.target.value))}
                        className="flex-1 h-1 accent-emerald-500"
                      />
                      <span className="text-xs text-gray-500 w-10 text-right">
                        {Math.round((layer.options?.opacity ?? 1) * 100)}%
                      </span>
                    </div>
                  )}

                  {/* 位置 */}
                  {(layer.type === "image" || layer.type === "text") && (
                    <div className="flex items-center gap-2">
                      <label className="text-xs text-gray-400 w-12">位置</label>
                      <input
                        type="number"
                        value={layer.options?.position_x ?? 0}
                        onChange={(e) => handlePositionChange(layer.id, "x", parseInt(e.target.value) || 0)}
                        className="w-16 px-1 py-0.5 text-xs bg-gray-700 rounded border border-gray-600"
                        placeholder="X"
                      />
                      <span className="text-xs text-gray-500">×</span>
                      <input
                        type="number"
                        value={layer.options?.position_y ?? 0}
                        onChange={(e) => handlePositionChange(layer.id, "y", parseInt(e.target.value) || 0)}
                        className="w-16 px-1 py-0.5 text-xs bg-gray-700 rounded border border-gray-600"
                        placeholder="Y"
                      />
                    </div>
                  )}

                  {/* 大小 */}
                  {layer.type === "image" && (
                    <div className="flex items-center gap-2">
                      <label className="text-xs text-gray-400 w-12">大小</label>
                      <input
                        type="number"
                        value={layer.options?.width ?? ""}
                        onChange={(e) => handleSizeChange(layer.id, "width", parseInt(e.target.value) || undefined)}
                        className="w-16 px-1 py-0.5 text-xs bg-gray-700 rounded border border-gray-600"
                        placeholder="宽"
                      />
                      <span className="text-xs text-gray-500">×</span>
                      <input
                        type="number"
                        value={layer.options?.height ?? ""}
                        onChange={(e) => handleSizeChange(layer.id, "height", parseInt(e.target.value) || undefined)}
                        className="w-16 px-1 py-0.5 text-xs bg-gray-700 rounded border border-gray-600"
                        placeholder="高"
                      />
                    </div>
                  )}

                  {/* 音量 */}
                  {layer.type === "audio" && (
                    <div className="flex items-center gap-2">
                      <label className="text-xs text-gray-400 w-12">音量</label>
                      <input
                        type="range"
                        min="0"
                        max="200"
                        value={(layer.options?.volume ?? 1) * 100}
                        onChange={(e) => handleVolumeChange(layer.id, parseInt(e.target.value))}
                        className="flex-1 h-1 accent-purple-500"
                      />
                      <span className="text-xs text-gray-500 w-10 text-right">
                        {Math.round((layer.options?.volume ?? 1) * 100)}%
                      </span>
                    </div>
                  )}

                  {/* 文字颜色 */}
                  {layer.type === "text" && (
                    <div className="flex items-center gap-2">
                      <label className="text-xs text-gray-400 w-12">颜色</label>
                      <input
                        type="color"
                        value={layer.options?.font_color ?? "#ffffff"}
                        onChange={(e) => onUpdateLayer?.(layer.id, { font_color: e.target.value })}
                        className="w-8 h-6 rounded cursor-pointer"
                      />
                      <input
                        type="number"
                        value={layer.options?.font_size ?? 48}
                        onChange={(e) => onUpdateLayer?.(layer.id, { font_size: parseInt(e.target.value) || 48 })}
                        className="w-16 px-1 py-0.5 text-xs bg-gray-700 rounded border border-gray-600"
                        placeholder="字号"
                      />
                      <span className="text-xs text-gray-500">px</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="p-4 text-center text-gray-500 text-sm">
            <p>暂无图层</p>
            <p className="text-xs mt-1">点击上方按钮添加</p>
          </div>
        )}
      </div>

      {/* 提示 */}
      <div className="p-2 border-t border-white/5 text-xs text-gray-500">
        <p>💡 添加图层后点击"开始"启动 FFmpeg 合成</p>
        <p className="mt-1">⚠️ 需要 FFmpeg 环境支持</p>
      </div>
    </div>
  );
}
