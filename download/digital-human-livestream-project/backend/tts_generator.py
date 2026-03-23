#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS Generator Module - TTS语音生成模块
使用z-ai-web-dev-sdk生成语音
"""

import os
import json
import subprocess
import asyncio
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from loguru import logger
from pydub import AudioSegment

from config import TTS_OUTPUT_DIR, TTS_SPEED, AUDIO_SAMPLE_RATE


class TTSGenerator:
    """TTS语音生成器"""
    
    def __init__(self):
        self.output_dir = TTS_OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Node.js TTS脚本路径
        self.tts_script_path = Path(__file__).parent / "tts_bridge.js"
    
    def generate_sync(self, text: str, output_file: Optional[str] = None, voice: str = "tongtong") -> Optional[str]:
        """
        同步生成TTS语音（调用Node.js脚本）
        
        Args:
            text: 要转换的文本
            output_file: 输出文件路径（不含扩展名）
            voice: 语音类型 (tongtong, xiaoyi, etc.)
        
        Returns:
            生成的音频文件路径，失败返回None
        """
        if not text or not text.strip():
            logger.warning("TTS文本为空，跳过生成")
            return None
        
        # 清理文本
        text = text.strip()
        
        # 生成输出文件名
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = str(self.output_dir / f"tts_{timestamp}")
        
        # 确保输出文件有.wav扩展名
        if not output_file.endswith('.wav'):
            output_file = f"{output_file}.wav"
        
        # 创建输出目录
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # 方法1：使用Node.js TTS桥接
            if self.tts_script_path.exists():
                return self._generate_via_nodejs(text, output_file, voice)
            
            # 方法2：使用edge-tts（Python库）
            return self._generate_via_edge_tts(text, output_file)
            
        except Exception as e:
            logger.error(f"TTS生成失败: {e}")
            return None
    
    def _generate_via_nodejs(self, text: str, output_file: str, voice: str) -> Optional[str]:
        """通过Node.js脚本生成TTS"""
        try:
            # 创建临时JSON文件传递参数
            temp_json = self.output_dir / "tts_params.json"
            with open(temp_json, 'w', encoding='utf-8') as f:
                json.dump({
                    "text": text,
                    "output": output_file,
                    "voice": voice,
                    "speed": TTS_SPEED
                }, f, ensure_ascii=False)
            
            # 调用Node.js脚本
            result = subprocess.run(
                ['node', str(self.tts_script_path), str(temp_json)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(Path(__file__).parent)
            )
            
            if result.returncode == 0:
                if Path(output_file).exists():
                    logger.info(f"TTS生成成功: {output_file}")
                    return output_file
                else:
                    logger.error(f"TTS文件未生成: {output_file}")
            else:
                logger.error(f"Node.js TTS失败: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error("TTS生成超时")
        except Exception as e:
            logger.error(f"Node.js TTS调用失败: {e}")
        
        return None
    
    def _generate_via_edge_tts(self, text: str, output_file: str) -> Optional[str]:
        """使用edge-tts生成语音（备选方案）"""
        try:
            import edge_tts
            
            # 中文语音
            voice = "zh-CN-XiaoxiaoNeural"
            
            async def _generate():
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(output_file)
            
            # 运行异步任务
            asyncio.run(_generate())
            
            if Path(output_file).exists():
                logger.info(f"Edge-TTS生成成功: {output_file}")
                return output_file
            else:
                logger.error(f"Edge-TTS文件未生成")
                
        except ImportError:
            logger.warning("edge-tts未安装，请运行: pip install edge-tts")
        except Exception as e:
            logger.error(f"Edge-TTS生成失败: {e}")
        
        return None
    
    def generate_for_news(self, news_items: List) -> List[dict]:
        """
        为新闻列表生成TTS音频
        
        Args:
            news_items: NewsItem对象列表
        
        Returns:
            包含新闻和音频路径的字典列表
        """
        results = []
        
        for i, news in enumerate(news_items):
            # 生成TTS文本
            tts_text = news.to_tts_text()
            
            # 生成音频文件
            output_file = str(self.output_dir / f"news_{news.id}.wav")
            
            audio_path = self.generate_sync(tts_text, output_file)
            
            if audio_path:
                results.append({
                    "news": news.to_dict(),
                    "audio_path": audio_path,
                    "duration": self._get_audio_duration(audio_path)
                })
            else:
                logger.warning(f"新闻 '{news.title}' TTS生成失败，跳过")
        
        logger.info(f"成功生成 {len(results)}/{len(news_items)} 条新闻语音")
        return results
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """获取音频时长（秒）"""
        try:
            audio = AudioSegment.from_wav(audio_path)
            return len(audio) / 1000.0
        except Exception as e:
            logger.error(f"获取音频时长失败: {e}")
            return 0.0
    
    def concatenate_audio(self, audio_files: List[str], output_file: str, 
                          crossfade_ms: int = 500) -> Optional[str]:
        """
        连接多个音频文件
        
        Args:
            audio_files: 音频文件路径列表
            output_file: 输出文件路径
            crossfade_ms: 淡入淡出时间（毫秒）
        
        Returns:
            输出文件路径
        """
        if not audio_files:
            return None
        
        try:
            combined = AudioSegment.empty()
            
            for i, audio_file in enumerate(audio_files):
                if not Path(audio_file).exists():
                    logger.warning(f"音频文件不存在: {audio_file}")
                    continue
                
                audio = AudioSegment.from_wav(audio_file)
                
                if i == 0:
                    combined = audio
                else:
                    combined = combined.append(audio, crossfade=crossfade_ms)
            
            # 导出
            combined.export(output_file, format="wav")
            logger.info(f"音频合并成功: {output_file}, 时长: {len(combined)/1000:.1f}秒")
            return output_file
            
        except Exception as e:
            logger.error(f"音频合并失败: {e}")
            return None


# 测试代码
if __name__ == "__main__":
    generator = TTSGenerator()
    
    # 测试生成
    test_text = "大家好，欢迎收看今日热点新闻。今天我们要关注的是人工智能领域的最新发展。"
    result = generator.generate_sync(test_text, "./test_output.wav")
    
    if result:
        print(f"测试成功，输出文件: {result}")
    else:
        print("测试失败")
