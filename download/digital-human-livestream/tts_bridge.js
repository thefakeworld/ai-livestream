#!/usr/bin/env node
/**
 * TTS Bridge Script - TTS桥接脚本
 * 使用z-ai-web-dev-sdk生成TTS语音
 * 
 * 使用方法:
 * node tts_bridge.js <params_json_file>
 * 
 * 或直接调用:
 * node tts_bridge.js --text "文本内容" --output "output.wav"
 */

import ZAI from "z-ai-web-dev-sdk";
import fs from "fs";
import path from "path";

// 支持的语音列表
const AVAILABLE_VOICES = [
    "tongtong",   // 通用女声
    "xiaoyi",     // 小艺
    "zhichu",     // 知初
    "zhitian",    // 知甜
    "zhiyan",     // 知言
    "zhitian_emo" // 知甜(情感版)
];

/**
 * 生成TTS语音
 * @param {string} text - 要转换的文本
 * @param {string} outputFile - 输出文件路径
 * @param {string} voice - 语音类型
 * @param {number} speed - 语速
 */
async function generateTTS(text, outputFile, voice = "tongtong", speed = 1.0) {
    try {
        console.log(`[TTS] 开始生成语音...`);
        console.log(`[TTS] 文本: ${text.substring(0, 50)}...`);
        console.log(`[TTS] 语音: ${voice}`);
        console.log(`[TTS] 输出: ${outputFile}`);
        
        const zai = await ZAI.create();
        
        const response = await zai.audio.tts.create({
            input: text,
            voice: voice,
            speed: speed,
            response_format: "wav",
            stream: false,
        });
        
        const arrayBuffer = await response.arrayBuffer();
        const buffer = Buffer.from(new Uint8Array(arrayBuffer));
        
        // 确保输出目录存在
        const outputDir = path.dirname(outputFile);
        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }
        
        fs.writeFileSync(outputFile, buffer);
        console.log(`[TTS] 语音生成成功: ${outputFile}`);
        console.log(`[TTS] 文件大小: ${(buffer.length / 1024).toFixed(2)} KB`);
        
        return { success: true, file: outputFile };
    } catch (err) {
        console.error(`[TTS] 生成失败:`, err?.message || err);
        return { success: false, error: err?.message || String(err) };
    }
}

/**
 * 从JSON参数文件运行
 */
async function runFromParamsFile(paramsFile) {
    try {
        const params = JSON.parse(fs.readFileSync(paramsFile, 'utf-8'));
        
        const result = await generateTTS(
            params.text,
            params.output,
            params.voice || "tongtong",
            params.speed || 1.0
        );
        
        // 写入结果文件
        const resultFile = paramsFile.replace('.json', '_result.json');
        fs.writeFileSync(resultFile, JSON.stringify(result, null, 2));
        
        process.exit(result.success ? 0 : 1);
    } catch (err) {
        console.error(`[TTS] 读取参数文件失败:`, err?.message || err);
        process.exit(1);
    }
}

/**
 * 从命令行参数运行
 */
async function runFromCommandLine() {
    const args = process.argv.slice(2);
    
    if (args.length === 0) {
        console.log(`
TTS Bridge - 语音生成工具

使用方法:
  node tts_bridge.js <params_json_file>
  node tts_bridge.js --text "文本" --output "output.wav" [--voice "tongtong"] [--speed 1.0]

可用语音:
  ${AVAILABLE_VOICES.join(', ')}

示例:
  node tts_bridge.js tts_params.json
  node tts_bridge.js --text "你好世界" --output "./hello.wav"
        `);
        process.exit(0);
    }
    
    // 检查是否是JSON文件参数
    if (args.length === 1 && args[0].endsWith('.json')) {
        await runFromParamsFile(args[0]);
        return;
    }
    
    // 解析命令行参数
    let text = "";
    let output = "./tts_output.wav";
    let voice = "tongtong";
    let speed = 1.0;
    
    for (let i = 0; i < args.length; i++) {
        switch (args[i]) {
            case '--text':
            case '-t':
                text = args[++i];
                break;
            case '--output':
            case '-o':
                output = args[++i];
                break;
            case '--voice':
            case '-v':
                voice = args[++i];
                break;
            case '--speed':
            case '-s':
                speed = parseFloat(args[++i]);
                break;
        }
    }
    
    if (!text) {
        console.error("[TTS] 错误: 请提供要转换的文本 (--text)");
        process.exit(1);
    }
    
    const result = await generateTTS(text, output, voice, speed);
    process.exit(result.success ? 0 : 1);
}

// 运行
runFromCommandLine();
