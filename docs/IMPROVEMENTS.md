# AI Livestream 改进记录

## 2024-03-23 启动问题修复

### 发现的问题

#### 1. Dataclass 缺少序列化方法 ❌→✅

| Dataclass | 文件 | 问题 | 状态 |
|-----------|------|------|------|
| `DirectorStatus` | `director/__init__.py` | 缺少 `to_dict()` | ✅ 已修复 |
| `TTSResult` | `services/tts_service.py` | 缺少 `to_dict()` | ✅ 已修复 |
| `VideoResult` | `services/video_service.py` | 缺少 `to_dict()` | ✅ 已修复 |
| `PlatformConfig` | `platforms/base.py` | 缺少 `to_dict()` | ✅ 已修复 |

**影响**: API 返回 health check 时报 `AttributeError: 'DirectorStatus' object has no attribute 'to_dict'`

#### 2. 文件权限问题 ⚠️

```
部分文件由 root 用户创建，导致普通用户无法修改：
- tsconfig.json
- next.config.ts  
- tailwind.config.ts
- postcss.config.mjs
- package.json
- start.sh
```

**临时方案**: 使用临时目录运行前端 `/tmp/ai-livestream-frontend`

**建议**: 统一使用非 root 用户创建文件，或在 Docker 中运行

#### 3. 缺少统一启动脚本 ✅

已创建 `start.sh` 启动脚本（因权限问题需要手动执行）

#### 4. Tailwind CSS 版本不匹配 ❌→✅

**问题**: `Module not found: Can't resolve 'tailwindcss'`

| 项目 | 问题值 | 正确值 |
|------|--------|--------|
| **安装版本** | `tailwindcss: ^3.4.0` | v3 |
| **CSS 语法** | `@import "tailwindcss";` | **v4 语法** ❌ |

**原因**: 使用了 Tailwind v4 的 CSS 导入语法，但项目安装的是 v3 版本

**修复**:
```css
/* 错误 (v4 语法) */
@import "tailwindcss";

/* 正确 (v3 语法) */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

#### 5. 外网访问 API 404 ❌→✅

**问题**: 外网访问 `/api/director` 返回 404

| 问题 | 原因 |
|------|------|
| 前端无 API 代理 | Next.js 未配置 rewrites |
| API 路径不一致 | 后端用 `/api/v1`，前端请求 `/api` |

**修复**: 添加 Next.js rewrites 配置

```typescript
// next.config.ts
async rewrites() {
  const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
  return [
    // 带 v1 前缀的路径
    {
      source: "/api/v1/:path*",
      destination: `${backendUrl}/api/v1/:path*`,
    },
    // 不带 v1 前缀的路径（兼容）
    {
      source: "/api/:path*",
      destination: `${backendUrl}/api/v1/:path*`,
    },
  ];
}
```

**同时更新 API 客户端**:
```typescript
// src/lib/api.ts
// 使用相对路径，通过 Next.js rewrites 代理到后端
const API_BASE = '/api/v1';
```

---

### 代码改进详情

#### DirectorStatus 添加 to_dict()
```python
@dataclass
class DirectorStatus:
    state: DirectorState = DirectorState.IDLE
    current_content: Optional[str] = None
    uptime: float = 0
    content_switched: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "current_content": self.current_content,
            "uptime": self.uptime,
            "content_switched": self.content_switched,
        }
```

#### TTSResult 添加 to_dict()
```python
@dataclass
class TTSResult:
    audio_path: Path
    duration: float
    text_hash: str
    voice: str

    def to_dict(self) -> dict:
        return {
            "audio_path": str(self.audio_path),
            "duration": self.duration,
            "text_hash": self.text_hash,
            "voice": self.voice,
        }
```

#### VideoResult 添加 to_dict()
```python
@dataclass
class VideoResult:
    path: Path
    duration: float
    resolution: str
    size_mb: float

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "duration": self.duration,
            "resolution": self.resolution,
            "size_mb": self.size_mb,
        }
```

#### PlatformConfig 添加 to_dict()
```python
@dataclass
class PlatformConfig:
    # ... existing fields ...

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "platform_type": self.platform_type,
            "rtmp_url": self.rtmp_url,
            "has_stream_key": bool(self.stream_key),
            "enabled": self.enabled,
            "configured": self.is_configured(),
        }
```

---

### 待改进项

| 问题 | 优先级 | 建议 |
|------|--------|------|
| 文件权限问题 | 高 | 统一使用非 root 用户或 Docker |
| 前端运行在临时目录 | 中 | 修复权限后使用正式目录 |
| 缺少进程管理 | 中 | 添加 PM2 或 systemd 服务 |
| 缺少日志轮转 | 低 | 配置 loguru 日志轮转 |
| 缺少监控告警 | 低 | 添加 Prometheus metrics |

---

## 如何避免重复问题

### 1. 版本兼容性检查清单

开发时需检查以下版本兼容性：

| 依赖 | 检查项 | 文件 |
|------|--------|------|
| **Tailwind CSS** | CSS 语法与安装版本匹配 | `globals.css`, `package.json` |
| **Next.js** | 配置语法匹配版本 | `next.config.ts` |
| **React** | Hooks 和组件语法 | 组件文件 |
| **TypeScript** | tsconfig 配置 | `tsconfig.json` |

### 2. 前后端 API 路径规范

**规则**: 前端访问后端 API 必须通过 Next.js rewrites 代理

**检查清单**:
- [ ] `next.config.ts` 配置 rewrites
- [ ] `src/lib/api.ts` 使用相对路径 `/api/v1`
- [ ] 后端 API 前缀与 rewrites 匹配
- [ ] 同时支持 `/api/v1/*` 和 `/api/*` 两种路径（兼容）

**环境变量**:
```bash
# 生产环境需要设置
BACKEND_URL=http://backend-service:8000
```

### 3. CSS 框架语法对照表

```css
/* Tailwind CSS v3 */
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Tailwind CSS v4 */
@import "tailwindcss";
```

### 4. Dataclass 序列化规范

**规则**: 所有可能在 API 返回中使用的 dataclass 必须实现 `to_dict()` 方法

**检查命令**:
```bash
# 查找没有 to_dict 的 dataclass
cd backend && grep -rn "@dataclass" --include="*.py" | cut -d: -f1 | sort -u | while read f; do
    if ! grep -q "def to_dict" "$f"; then
        echo "缺少 to_dict: $f"
    fi
done
```

### 5. 文件权限规范

**规则**: 统一使用非 root 用户创建文件

**检查命令**:
```bash
# 查找 root 创建的文件
find /home/z/my-project/ai-livestream -user root -type f
```

**修复方法**:
```bash
# 重新创建文件（保留内容）
for file in $(find . -user root -type f); do
    content=$(cat "$file")
    rm -f "$file"
    echo "$content" > "$file"
done
```

### 6. 启动前检查脚本

建议在 `package.json` 中添加预检查：

```json
{
  "scripts": {
    "precheck": "node scripts/check-deps.mjs",
    "dev": "npm run precheck && next dev"
  }
}
```

`scripts/check-deps.mjs`:
```javascript
import { readFileSync, existsSync } from 'fs';

// 检查 Tailwind 版本
const pkg = JSON.parse(readFileSync('./package.json'));
const tailwindVersion = pkg.devDependencies.tailwindcss;
const isV4 = tailwindVersion?.startsWith('^4');

// 检查 CSS 语法
const css = readFileSync('./src/app/globals.css', 'utf-8');
const usesV4Syntax = css.includes('@import "tailwindcss"');

if (isV4 !== usesV4Syntax) {
  console.error('❌ Tailwind CSS 版本与语法不匹配!');
  console.error(`   安装版本: ${tailwindVersion}`);
  console.error(`   CSS 语法: ${usesV4Syntax ? 'v4 (@import)' : 'v3 (@tailwind)'}`);
  process.exit(1);
}

console.log('✅ 依赖检查通过');
```

---

### 快速启动命令

```bash
# 方式1: 使用启动脚本（需要修复权限后）
cd /home/z/my-project/ai-livestream
bash start.sh

# 方式2: 手动启动
# 后端
cd /home/z/my-project/ai-livestream/backend
PYTHONPATH=$(pwd) /home/z/.local/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# 前端（使用临时目录）
cp -r /home/z/my-project/ai-livestream/frontend/* /tmp/ai-livestream-frontend/
cd /tmp/ai-livestream-frontend
npm run dev
```

### 服务地址

| 服务 | 地址 |
|------|------|
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/health |
| 前端界面 | http://localhost:3000 |
| 导播控制台 | http://localhost:3000/director |
