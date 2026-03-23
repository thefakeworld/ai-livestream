import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  
  // 允许外网预览域名访问
  allowedDevOrigins: [
    'preview-chat-e999048d-f20f-40ea-833a-fbec6ace84c1.space.z.ai',
    '.space.z.ai',  // 允许所有 space.z.ai 子域名
  ],
  
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "/api/v1",
  },
  
  // API 代理配置 - 将 /api 请求转发到后端
  async rewrites() {
    // 从环境变量获取后端地址，默认本地开发地址
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
    console.log('[Next.js] API Proxy Backend:', backendUrl);
    
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
  },
};

export default nextConfig;
