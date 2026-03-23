"use client";

import { Layer } from "./LayerManager";

interface LayerPreviewOverlayProps {
  layers: Layer[];
  className?: string;
}

/**
 * 图层预览叠加组件
 * 在视频播放器上叠加显示图片层、文字层等内容
 */
export default function LayerPreviewOverlay({ layers, className = "" }: LayerPreviewOverlayProps) {
  // 只显示可见的图层，按顺序排列
  const visibleLayers = layers
    .filter(l => l.visible && l.type !== "video" && l.type !== "audio")
    .sort((a, b) => a.order - b.order);

  if (visibleLayers.length === 0) {
    return null;
  }

  return (
    <div className={`absolute inset-0 pointer-events-none overflow-hidden ${className}`}>
      {visibleLayers.map((layer) => {
        const { options, type, source, name } = layer;
        
        // 图片层
        if (type === "image" && source) {
          return (
            <div
              key={layer.id}
              className="absolute"
              style={{
                left: options.position_x,
                top: options.position_y,
                width: options.width || "auto",
                height: options.height || "auto",
                opacity: options.opacity,
              }}
            >
              <img
                src={source}
                alt={name}
                className="max-w-full max-h-full object-contain"
                onError={(e) => {
                  // 图片加载失败时隐藏
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
            </div>
          );
        }
        
        // 文字层
        if (type === "text") {
          return (
            <div
              key={layer.id}
              className="absolute"
              style={{
                left: options.position_x,
                top: options.position_y,
                fontSize: options.font_size || 48,
                color: options.font_color || "#ffffff",
                fontFamily: options.font_family || "Arial, sans-serif",
                opacity: options.opacity,
                textShadow: "2px 2px 4px rgba(0,0,0,0.5)", // 文字阴影增加可读性
                whiteSpace: "nowrap",
              }}
            >
              {name}
            </div>
          );
        }
        
        return null;
      })}
    </div>
  );
}
