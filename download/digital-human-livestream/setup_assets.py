#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源准备脚本 - 生成默认数字人背景图
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_default_background():
    """创建默认背景图"""
    width, height = 1280, 720
    
    # 创建渐变背景
    img = Image.new('RGB', (width, height), (25, 35, 60))
    draw = ImageDraw.Draw(img)
    
    # 绘制渐变
    for y in range(height):
        ratio = y / height
        r = int(25 + 40 * ratio)
        g = int(35 + 50 * ratio)
        b = int(60 + 80 * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # 添加装饰元素
    # 左侧装饰条
    draw.rectangle([(0, 0), (10, height)], fill=(70, 130, 180))
    
    # 底部装饰
    draw.rectangle([(0, height-150), (width, height)], fill=(30, 40, 70))
    
    # 添加标题文字
    try:
        # 尝试加载字体
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # 标题
    draw.text((50, 50), "Live News", font=font_large, fill=(255, 255, 255))
    
    # 底部文字区域
    draw.rectangle([(20, height-140), (width-20, height-20)], outline=(70, 130, 180), width=2)
    draw.text((30, height-130), "News content will be displayed here...", font=font_small, fill=(200, 200, 200))
    
    # 保存
    output_path = "assets/video/digital_human.png"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)
    print(f"默认背景图已创建: {output_path}")
    
    return output_path

if __name__ == "__main__":
    create_default_background()
