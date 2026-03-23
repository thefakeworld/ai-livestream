"use client";

import { useState, useRef, useEffect } from "react";

export interface DanmakuMessage {
  id: string;
  user: string;
  content: string;
  platform: "bilibili" | "douyin" | "youtube" | "tiktok" | "other";
  timestamp: number;
  avatar?: string;
}

export interface AISuggestion {
  id: string;
  type: "switch_content" | "reply" | "greeting" | "action";
  confidence: number;
  message: DanmakuMessage;
  action?: {
    type: "switch_music" | "switch_video" | "play_next";
    target?: string;
  };
  reply?: string;
}

interface DanmakuPanelProps {
  messages: DanmakuMessage[];
  suggestions: AISuggestion[];
  onSendMessage: (message: string) => void;
  onAcceptSuggestion: (suggestion: AISuggestion) => void;
  onDismissSuggestion: (suggestionId: string) => void;
  autoMode: boolean;
  onToggleAutoMode: () => void;
}

export default function DanmakuPanel({
  messages,
  suggestions,
  onSendMessage,
  onAcceptSuggestion,
  onDismissSuggestion,
  autoMode,
  onToggleAutoMode,
}: DanmakuPanelProps) {
  const [inputText, setInputText] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const getPlatformIcon = (platform: string) => {
    switch (platform) {
      case "bilibili": return "📺";
      case "douyin": return "🎵";
      case "youtube": return "▶️";
      case "tiktok": return "🎵";
      default: return "💬";
    }
  };

  const getPlatformColor = (platform: string) => {
    switch (platform) {
      case "bilibili": return "text-pink-400";
      case "douyin": return "text-cyan-400";
      case "youtube": return "text-red-400";
      case "tiktok": return "text-white";
      default: return "text-gray-400";
    }
  };

  const getSuggestionIcon = (type: string) => {
    switch (type) {
      case "switch_content": return "🔄";
      case "reply": return "💬";
      case "greeting": return "👋";
      case "action": return "⚡";
      default: return "🤖";
    }
  };

  const handleSend = () => {
    if (inputText.trim()) {
      onSendMessage(inputText.trim());
      setInputText("");
    }
  };

  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp);
    return `${date.getHours().toString().padStart(2, "0")}:${date.getMinutes().toString().padStart(2, "0")}`;
  };

  return (
    <div className="flex flex-col h-full">
      {/* 标题和 AI 模式开关 */}
      <div className="p-3 border-b border-white/5 flex items-center justify-between">
        <h3 className="font-semibold text-sm flex items-center gap-2">
          <span>💬</span> 弹幕互动
          {messages.length > 0 && (
            <span className="text-xs text-gray-500">({messages.length})</span>
          )}
        </h3>
        <button
          onClick={onToggleAutoMode}
          className={`px-2 py-1 rounded text-xs flex items-center gap-1 ${
            autoMode 
              ? "bg-emerald-500/20 text-emerald-400" 
              : "bg-gray-700 text-gray-400"
          }`}
        >
          <span>🤖</span>
          {autoMode ? "自动" : "手动"}
        </button>
      </div>

      {/* AI 建议区域 */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="border-b border-white/5 bg-emerald-500/5">
          <div className="p-2 flex items-center justify-between">
            <span className="text-xs font-medium text-emerald-400">🤖 AI 建议</span>
            <button 
              onClick={() => setShowSuggestions(false)}
              className="text-xs text-gray-500 hover:text-gray-400"
            >
              隐藏
            </button>
          </div>
          <div className="max-h-32 overflow-y-auto space-y-1 p-2 pt-0">
            {suggestions.map((suggestion) => (
              <div 
                key={suggestion.id}
                className="p-2 bg-gray-800/50 rounded-lg text-xs"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span>{getSuggestionIcon(suggestion.type)}</span>
                  <span className="text-gray-400 truncate flex-1">
                    "{suggestion.message.content}"
                  </span>
                  <span className="text-emerald-400 font-medium">
                    {Math.round(suggestion.confidence * 100)}%
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-gray-300 flex-1">
                    {suggestion.reply || `建议: ${suggestion.action?.type || ""}`}
                  </span>
                  <button
                    onClick={() => onAcceptSuggestion(suggestion)}
                    className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 rounded hover:bg-emerald-500/30"
                  >
                    执行
                  </button>
                  <button
                    onClick={() => onDismissSuggestion(suggestion.id)}
                    className="px-2 py-0.5 bg-gray-700 text-gray-400 rounded hover:bg-gray-600"
                  >
                    忽略
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 弹幕列表 */}
      <div className="flex-1 overflow-y-auto">
        {messages.length > 0 ? (
          <div className="p-2 space-y-1">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className="p-1.5 rounded hover:bg-white/5 transition-all group"
              >
                <div className="flex items-start gap-2">
                  <span className="text-xs">{getPlatformIcon(msg.platform)}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1">
                      <span className={`text-xs font-medium ${getPlatformColor(msg.platform)} truncate`}>
                        {msg.user}
                      </span>
                      <span className="text-xs text-gray-600">{formatTime(msg.timestamp)}</span>
                    </div>
                    <p className="text-xs text-gray-300 break-all">{msg.content}</p>
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        ) : (
          <div className="p-4 text-center text-gray-500 text-sm">
            <p>暂无弹幕</p>
            <p className="text-xs mt-1">连接平台后显示弹幕</p>
          </div>
        )}
      </div>

      {/* 发送消息 */}
      <div className="p-2 border-t border-white/5">
        <div className="flex gap-1">
          <input
            type="text"
            placeholder="发送消息..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && handleSend()}
            className="flex-1 px-3 py-1.5 text-sm bg-gray-700/50 rounded-lg border border-gray-600 focus:border-emerald-500 focus:outline-none"
          />
          <button
            onClick={handleSend}
            disabled={!inputText.trim()}
            className="px-3 py-1.5 bg-emerald-500/20 text-emerald-400 rounded-lg text-sm hover:bg-emerald-500/30 disabled:opacity-50"
          >
            发送
          </button>
        </div>
      </div>

      {/* 快捷操作 */}
      <div className="p-2 border-t border-white/5 flex gap-1">
        <button className="flex-1 py-1.5 text-xs bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30">
          👋 欢迎新人
        </button>
        <button className="flex-1 py-1.5 text-xs bg-purple-500/20 text-purple-400 rounded-lg hover:bg-purple-500/30">
          🙏 感谢关注
        </button>
      </div>
    </div>
  );
}
