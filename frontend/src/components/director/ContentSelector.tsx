"use client";

import { useState } from "react";

export interface ContentItem {
  id: string;
  type: "video" | "music" | "news" | "image";
  name: string;
  title: string;
  url?: string;
  thumbnail?: string;
  duration: number;
  artist?: string;
}

interface ContentSelectorProps {
  contents: ContentItem[];
  currentContent: ContentItem | null;
  onSelect: (item: ContentItem) => void;
}

export default function ContentSelector({ contents, currentContent, onSelect }: ContentSelectorProps) {
  const [filter, setFilter] = useState<string>("all");
  const [search, setSearch] = useState("");

  const filteredContents = contents.filter(item => {
    if (filter !== "all" && item.type !== filter) return false;
    if (search && !item.title.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "news": return "📰";
      case "music": return "🎵";
      case "video": return "🎬";
      case "image": return "🖼️";
      default: return "📄";
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case "news": return "bg-blue-500/20 text-blue-400";
      case "music": return "bg-purple-500/20 text-purple-400";
      case "video": return "bg-orange-500/20 text-orange-400";
      case "image": return "bg-green-500/20 text-green-400";
      default: return "bg-gray-500/20 text-gray-400";
    }
  };

  const formatDuration = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="flex flex-col h-full">
      {/* 标题 */}
      <div className="p-3 border-b border-white/5">
        <h3 className="font-semibold text-sm flex items-center gap-2">
          <span>📋</span> 内容选择
        </h3>
      </div>

      {/* 搜索和筛选 */}
      <div className="p-2 space-y-2 border-b border-white/5">
        <input
          type="text"
          placeholder="搜索内容..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-3 py-1.5 text-sm bg-gray-700/50 rounded-lg border border-gray-600 focus:border-emerald-500 focus:outline-none"
        />
        <div className="flex gap-1 flex-wrap">
          {["all", "video", "music", "image"].map((type) => (
            <button
              key={type}
              onClick={() => setFilter(type)}
              className={`px-2 py-1 rounded text-xs transition-all ${
                filter === type 
                  ? "bg-emerald-500/20 text-emerald-400" 
                  : "bg-gray-700 text-gray-400 hover:bg-gray-600"
              }`}
            >
              {type === "all" ? "全部" : type === "video" ? "🎬" : type === "music" ? "🎵" : "🖼️"}
            </button>
          ))}
        </div>
      </div>

      {/* 内容列表 */}
      <div className="flex-1 overflow-y-auto">
        {filteredContents.length > 0 ? (
          <div className="divide-y divide-white/5">
            {filteredContents.map((item) => (
              <button
                key={item.id}
                onClick={() => onSelect(item)}
                className={`w-full p-2 flex items-center gap-2 hover:bg-white/5 transition-all text-left ${
                  currentContent?.id === item.id ? "bg-emerald-500/10 border-l-2 border-emerald-500" : ""
                }`}
              >
                {item.thumbnail ? (
                  <img 
                    src={item.thumbnail} 
                    alt={item.title}
                    className="w-12 h-8 rounded object-cover bg-gray-700 flex-shrink-0"
                  />
                ) : (
                  <div className="w-12 h-8 rounded bg-gray-700 flex items-center justify-center text-sm flex-shrink-0">
                    {getTypeIcon(item.type)}
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium truncate">{item.title}</p>
                  <p className="text-xs text-gray-500">
                    {item.artist ? `${item.artist} • ` : ""}{formatDuration(item.duration)}
                  </p>
                </div>
                <span className={`px-1.5 py-0.5 rounded text-xs ${getTypeColor(item.type)}`}>
                  {item.type === "video" ? "视频" : item.type === "music" ? "音乐" : item.type === "image" ? "图片" : "新闻"}
                </span>
              </button>
            ))}
          </div>
        ) : (
          <div className="p-4 text-center text-gray-500 text-sm">
            <p>暂无内容</p>
          </div>
        )}
      </div>

      {/* 快捷操作 */}
      <div className="p-2 border-t border-white/5">
        <button className="w-full py-1.5 text-xs bg-emerald-500/20 text-emerald-400 rounded-lg hover:bg-emerald-500/30">
          + 添加本地文件
        </button>
      </div>
    </div>
  );
}
