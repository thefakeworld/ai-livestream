"""
Layer Compositor - 多图层合成服务
使用 FFmpeg filter_complex 实现视频、图片、文字、音频的多层叠加
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import subprocess
import threading
import time
import os
import tempfile
import shutil
import atexit

from core.config import get_settings
from core.logger import get_logger

logger = get_logger("layer_compositor")


class LayerType(Enum):
    VIDEO = "video"
    IMAGE = "image"
    TEXT = "text"
    AUDIO = "audio"


@dataclass
class LayerOptions:
    """图层选项"""
    position_x: int = 0
    position_y: int = 0
    width: Optional[int] = None
    height: Optional[int] = None
    opacity: float = 1.0
    # 文字特有属性
    font_size: int = 48
    font_color: str = "white"
    font_family: str = "Arial"
    # 音频特有属性
    volume: float = 1.0


@dataclass
class Layer:
    """图层"""
    id: str
    type: LayerType
    name: str
    source: str  # 文件路径或URL
    visible: bool = True
    order: int = 0
    options: LayerOptions = field(default_factory=LayerOptions)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "source": self.source,
            "visible": self.visible,
            "order": self.order,
            "options": {
                "position_x": self.options.position_x,
                "position_y": self.options.position_y,
                "width": self.options.width,
                "height": self.options.height,
                "opacity": self.options.opacity,
                "font_size": self.options.font_size,
                "font_color": self.options.font_color,
                "font_family": self.options.font_family,
                "volume": self.options.volume,
            }
        }


class LayerCompositor:
    """多图层合成器 - 生成真实视频流"""

    def __init__(self):
        self.settings = get_settings()
        self.layers: List[Layer] = []
        self._process: Optional[subprocess.Popen] = None
        self._running = False
        self._hls_dir: Optional[str] = None
        self._playlist_path: Optional[str] = None
        self._start_time: Optional[float] = None
        
        # 创建 HLS 输出目录
        self._setup_hls_dir()
        
        # 注册清理函数
        atexit.register(self.stop_composite)

    def _setup_hls_dir(self):
        """设置 HLS 输出目录"""
        self._hls_dir = "/tmp/hls_stream"
        os.makedirs(self._hls_dir, exist_ok=True)
        self._playlist_path = os.path.join(self._hls_dir, "stream.m3u8")
        logger.info(f"HLS output directory: {self._hls_dir}")

    def add_layer(self, layer: Layer) -> bool:
        """添加图层"""
        try:
            # 检查重复
            if any(l.id == layer.id for l in self.layers):
                logger.warning(f"Layer {layer.id} already exists, updating instead")
                return self.update_layer(layer.id, layer.to_dict())

            self.layers.append(layer)
            self.layers.sort(key=lambda l: l.order)
            logger.info(f"Added layer: {layer.name} (type={layer.type.value})")
            return True
        except Exception as e:
            logger.error(f"Failed to add layer: {e}")
            return False

    def remove_layer(self, layer_id: str) -> bool:
        """移除图层"""
        for i, layer in enumerate(self.layers):
            if layer.id == layer_id:
                self.layers.pop(i)
                logger.info(f"Removed layer: {layer_id}")
                return True
        return False

    def update_layer(self, layer_id: str, updates: Dict[str, Any]) -> bool:
        """更新图层属性"""
        for layer in self.layers:
            if layer.id == layer_id:
                # 更新基本属性
                if "visible" in updates:
                    layer.visible = updates["visible"]
                if "order" in updates:
                    layer.order = updates["order"]
                if "name" in updates:
                    layer.name = updates["name"]
                if "source" in updates:
                    layer.source = updates["source"]

                # 更新选项
                if "options" in updates:
                    opts = updates["options"]
                    if isinstance(opts, dict):
                        if "position_x" in opts:
                            layer.options.position_x = opts["position_x"]
                        if "position_y" in opts:
                            layer.options.position_y = opts["position_y"]
                        if "width" in opts:
                            layer.options.width = opts["width"]
                        if "height" in opts:
                            layer.options.height = opts["height"]
                        if "opacity" in opts:
                            layer.options.opacity = max(0, min(1, float(opts["opacity"])))
                        if "font_size" in opts:
                            layer.options.font_size = opts["font_size"]
                        if "font_color" in opts:
                            layer.options.font_color = opts["font_color"]
                        if "volume" in opts:
                            layer.options.volume = max(0, min(2, float(opts["volume"])))

                # 重新排序
                self.layers.sort(key=lambda l: l.order)
                logger.info(f"Updated layer: {layer_id}")
                
                # 如果正在运行，重启合成以应用更改
                if self._running:
                    self._restart_composite()
                    
                return True
        return False

    def get_layer(self, layer_id: str) -> Optional[Layer]:
        """获取图层"""
        for layer in self.layers:
            if layer.id == layer_id:
                return layer
        return None

    def get_all_layers(self) -> List[Layer]:
        """获取所有图层"""
        return sorted(self.layers, key=lambda l: l.order)

    def clear_layers(self):
        """清除所有图层"""
        self.layers.clear()
        logger.info("Cleared all layers")

    def get_status(self) -> Dict[str, Any]:
        """获取合成状态"""
        return {
            "is_running": self._running,
            "layer_count": len(self.layers),
            "visible_count": len([l for l in self.layers if l.visible]),
            "hls_path": self._playlist_path,
            "uptime": time.time() - self._start_time if self._start_time else 0,
            "layers": [l.to_dict() for l in self.layers],
        }

    def build_filter_complex(self) -> str:
        """构建 FFmpeg filter_complex 字符串"""
        filters = []
        video_layers = [l for l in self.layers if l.type == LayerType.VIDEO and l.visible]
        image_layers = [l for l in self.layers if l.type == LayerType.IMAGE and l.visible]
        text_layers = [l for l in self.layers if l.type == LayerType.TEXT and l.visible]
        audio_layers = [l for l in self.layers if l.type == LayerType.AUDIO and l.visible]

        video_filter_chain = []
        audio_filter_chain = []
        
        input_idx = 0

        # 1. 处理主视频（如果有）
        if video_layers:
            main_video = video_layers[0]
            scale_filter = f"[{input_idx}:v]scale={self.settings.VIDEO_WIDTH}:{self.settings.VIDEO_HEIGHT}"
            if main_video.options.opacity < 1.0:
                scale_filter += f",format=rgba,colorchannelmixer=aa={main_video.options.opacity}"
            scale_filter += "[base]"
            video_filter_chain.append(scale_filter)
            input_idx += 1
            current_video = "[base]"
        else:
            # 使用测试图案作为基础
            video_filter_chain.append(
                f"color=c=black:s={self.settings.VIDEO_WIDTH}x{self.settings.VIDEO_HEIGHT}:r={self.settings.VIDEO_FPS}[base]"
            )
            current_video = "[base]"

        # 2. 叠加图片层
        for i, img_layer in enumerate(image_layers):
            img_label = f"[img{i}]"
            overlay_label = f"[v{i}]"

            # 图片处理
            img_filter_parts = []
            if img_layer.options.width and img_layer.options.height:
                img_filter_parts.append(f"scale={img_layer.options.width}:{img_layer.options.height}")
            if img_layer.options.opacity < 1.0:
                img_filter_parts.append(f"format=rgba,colorchannelmixer=aa={img_layer.options.opacity}")
            
            if img_filter_parts:
                img_filter = f"[{input_idx}:v]{','.join(img_filter_parts)}{img_label}"
                video_filter_chain.append(img_filter)
                source_label = img_label
            else:
                source_label = f"[{input_idx}:v]"

            # 叠加
            x = img_layer.options.position_x
            y = img_layer.options.position_y
            overlay_filter = f"{current_video}{source_label}overlay={x}:{y}{overlay_label}"
            video_filter_chain.append(overlay_filter)

            current_video = overlay_label
            input_idx += 1

        # 3. 添加文字层
        for i, text_layer in enumerate(text_layers):
            text_label = f"[vtext{i}]"
            x = text_layer.options.position_x
            y = text_layer.options.position_y
            font_size = text_layer.options.font_size
            font_color = text_layer.options.font_color

            # 转义文字内容
            text_content = text_layer.source.replace("'", "\\'").replace(":", "\\:")
            drawtext_filter = f"{current_video}drawtext=text='{text_content}':fontsize={font_size}:fontcolor={font_color}:x={x}:y={y}"
            if text_layer.options.opacity < 1.0:
                drawtext_filter += f":alpha={text_layer.options.opacity}"
            drawtext_filter += text_label
            video_filter_chain.append(drawtext_filter)

            current_video = text_label

        # 最终视频输出
        video_filter_chain.append(f"{current_video}copy[outv]")
        filters.append(";".join(video_filter_chain))

        # 4. 处理音频
        if audio_layers:
            audio_inputs = []
            for i, audio_layer in enumerate(audio_layers):
                vol = audio_layer.options.volume
                audio_filter = f"[{input_idx}:a]volume={vol}[audio{i}]"
                audio_filter_chain.append(audio_filter)
                audio_inputs.append(f"[audio{i}]")
                input_idx += 1

            if len(audio_inputs) > 1:
                amix_filter = f"{''.join(audio_inputs)}amix=inputs={len(audio_inputs)}:duration=longest[aout]"
            else:
                amix_filter = f"{audio_inputs[0]}acopy[aout]"
            audio_filter_chain.append(amix_filter)
            filters.append(";".join(audio_filter_chain))

        return ";".join(filters)

    def build_command(self, duration: float = 3600) -> List[str]:
        """构建完整的 FFmpeg 命令"""
        cmd = ["ffmpeg", "-y"]

        video_layers = [l for l in self.layers if l.type == LayerType.VIDEO and l.visible]
        image_layers = [l for l in self.layers if l.type == LayerType.IMAGE and l.visible]
        audio_layers = [l for l in self.layers if l.type == LayerType.AUDIO and l.visible]

        # 视频输入
        if video_layers:
            for layer in video_layers[:1]:  # 主视频
                if layer.source.startswith(("http://", "https://", "rtmp://")):
                    cmd.extend(["-i", layer.source])
                elif os.path.exists(layer.source):
                    cmd.extend(["-stream_loop", "-1", "-i", layer.source])
                else:
                    logger.warning(f"Video source not found: {layer.source}")

        # 图片输入
        for layer in image_layers:
            if layer.source.startswith(("http://", "https://")):
                # 网络图片 - 先下载或使用 FFmpeg 直接读取
                cmd.extend(["-loop", "1", "-i", layer.source, "-t", str(duration)])
            elif os.path.exists(layer.source):
                cmd.extend(["-loop", "1", "-i", layer.source, "-t", str(duration)])
            else:
                logger.warning(f"Image source not found: {layer.source}")

        # 音频输入
        for layer in audio_layers:
            if layer.source.startswith(("http://", "https://")):
                cmd.extend(["-i", layer.source])
            elif os.path.exists(layer.source):
                cmd.extend(["-stream_loop", "-1", "-i", layer.source])

        # 如果没有视频输入，使用 lavfi 生成测试图案
        if not video_layers:
            cmd.extend([
                "-f", "lavfi",
                "-i", f"color=c=black:s={self.settings.VIDEO_WIDTH}x{self.settings.VIDEO_HEIGHT}:r={self.settings.VIDEO_FPS}",
            ])

        # 构建 filter_complex
        filter_complex = self.build_filter_complex()
        cmd.extend(["-filter_complex", filter_complex])

        # 映射输出
        cmd.extend(["-map", "[outv]"])
        if audio_layers:
            cmd.extend(["-map", "[aout]"])
        elif not video_layers:
            # 添加静音
            cmd.extend([
                "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                "-map", "2:a"
            ])

        # 编码设置
        cmd.extend([
            "-c:v", self.settings.VIDEO_CODEC,
            "-preset", self.settings.VIDEO_PRESET,
            "-b:v", self.settings.VIDEO_BITRATE,
            "-pix_fmt", "yuv420p",
            "-g", "60",
            "-c:a", self.settings.AUDIO_CODEC,
            "-b:a", self.settings.AUDIO_BITRATE,
            "-ar", "44100",
        ])

        # HLS 输出
        cmd.extend([
            "-f", "hls",
            "-hls_time", "2",
            "-hls_list_size", "5",
            "-hls_flags", "delete_segments+append_list",
            "-hls_segment_filename", os.path.join(self._hls_dir, "segment_%03d.ts"),
            self._playlist_path
        ])

        return cmd

    def start_composite(self, output_path: str = None, duration: float = 3600) -> bool:
        """启动合成"""
        if self._running:
            logger.warning("Compositor already running, restarting...")
            self.stop_composite()

        try:
            cmd = self.build_command(duration)
            logger.info(f"Starting compositor with {len(self.layers)} layers")
            logger.debug(f"Command: {' '.join(cmd[:15])}...")

            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self._running = True
            self._start_time = time.time()
            
            # 启动日志监控线程
            threading.Thread(target=self._monitor_output, daemon=True).start()
            
            logger.info("Compositor started successfully")
            logger.info(f"HLS stream available at: {self._playlist_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to start compositor: {e}")
            return False

    def _monitor_output(self):
        """监控 FFmpeg 输出"""
        if not self._process:
            return
            
        while self._running and self._process:
            line = self._process.stderr.readline()
            if not line:
                break
            line_str = line.decode('utf-8', errors='ignore').strip()
            if line_str:
                logger.debug(f"FFmpeg: {line_str}")

    def _restart_composite(self):
        """重启合成以应用更改"""
        if self._running:
            logger.info("Restarting composite to apply layer changes...")
            self.stop_composite()
            time.sleep(0.5)
            self.start_composite()

    def stop_composite(self) -> bool:
        """停止合成"""
        if not self._running or not self._process:
            return True

        try:
            self._process.terminate()
            self._process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait()
        except Exception as e:
            logger.error(f"Error stopping process: {e}")

        self._running = False
        self._process = None
        self._start_time = None
        logger.info("Compositor stopped")
        return True

    @property
    def is_running(self) -> bool:
        return self._running

    def get_hls_path(self) -> Optional[str]:
        """获取 HLS 播放列表路径"""
        return self._playlist_path if self._running else None


# 全局实例
_compositor: Optional[LayerCompositor] = None


def get_compositor() -> LayerCompositor:
    """获取全局合成器实例"""
    global _compositor
    if _compositor is None:
        _compositor = LayerCompositor()
    return _compositor
