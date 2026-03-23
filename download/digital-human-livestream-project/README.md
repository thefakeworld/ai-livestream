# 数字人多平台直播系统

## 项目概述
- AI 数字人无人值守直播
- 自动新闻抓取 + TTS 语音合成
- 多平台同时推流（10+ 平台）
- Web 导播台控制面板

## 快速开始

### 后端 (Python)
```bash
cd backend
pip install -r requirements.txt
# 编辑 config.py 配置推流密钥
python3 intelligent_director.py
```

### 前端 (Next.js)
```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:3000/director
```

## 支持平台
YouTube, TikTok, B站, 抖音, Twitch, Facebook, 快手, 虎牙, 斗鱼, 小红书

## 文件说明
- `intelligent_director.py` - 智能导播主程序
- `multi_platform_config.py` - 多平台配置
- `streamer.py` - 推流核心
- `news_fetcher.py` - 新闻抓取
- `tts_generator.py` - TTS 语音生成

---
版本: 1.0.0
打包时间: 2026-03-22
