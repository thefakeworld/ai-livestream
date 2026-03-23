# 发布检查清单

## 发布前必检项

### 1. 代码质量

- [ ] 所有单元测试通过
  ```bash
  cd backend && pytest tests/ -v
  cd frontend && npm test
  ```

- [ ] 代码风格检查通过
  ```bash
  cd frontend && npm run lint
  cd backend && mypy api/ --ignore-missing-imports
  ```

- [ ] 无 TypeScript 类型错误
  ```bash
  cd frontend && npm run build
  ```

### 2. API 契约验证

- [ ] OpenAPI 规范已更新 (`api-spec.yaml`)
- [ ] 前后端 API 路径一致
- [ ] 契约测试通过
  ```bash
  cd backend && pytest tests/contract/ -v
  ```

- [ ] API 接口验证脚本通过
  ```bash
  ./scripts/verify-apis.sh
  ```

### 3. 功能测试

- [ ] 开始直播功能正常
- [ ] 停止直播功能正常
- [ ] 切换内容功能正常
- [ ] 平台列表显示正常
- [ ] 内容库显示正常

### 4. 兼容性测试

- [ ] 本地环境测试通过
- [ ] 外网访问测试通过
- [ ] 跨浏览器兼容 (Chrome, Firefox, Safari)
- [ ] 移动端响应式布局正常

### 5. 安全检查

- [ ] 无敏感信息泄露 (API Key, Stream Key)
- [ ] CORS 配置正确
- [ ] 输入验证完善
- [ ] 错误信息不暴露内部细节

### 6. 性能检查

- [ ] 页面加载时间 < 3s
- [ ] API 响应时间 < 500ms
- [ ] 无内存泄漏
- [ ] 无明显 CPU 占用异常

### 7. 文档更新

- [ ] README.md 已更新
- [ ] API 文档已更新
- [ ] CHANGELOG.md 已更新
- [ ] 配置说明已更新

### 8. 部署准备

- [ ] 环境变量已配置
- [ ] 数据库迁移脚本已准备
- [ ] 回滚方案已准备
- [ ] 监控告警已配置

---

## 发布流程

### Step 1: 代码冻结
```bash
# 创建发布分支
git checkout -b release/v$(date +'%Y.%m.%d')
```

### Step 2: 版本更新
```bash
# 更新版本号
# backend/core/config.py: APP_VERSION
# frontend/package.json: version
```

### Step 3: 运行所有测试
```bash
# 后端测试
cd backend && pytest tests/ -v --cov

# 前端测试
cd frontend && npm run lint && npm run build

# API 验证
./scripts/verify-apis.sh
```

### Step 4: 提交发布
```bash
git add .
git commit -m "chore: release v$(date +'%Y.%m.%d')"
git tag -a v$(date +'%Y.%m.%d') -m "Release $(date +'%Y.%m.%d')"
git push origin main --tags
```

### Step 5: 部署后验证
```bash
# 健康检查
curl https://your-domain/health

# API 检查
curl https://your-domain/api/v1/director/status
curl https://your-domain/api/v1/platform/list
```

---

## 回滚方案

### 快速回滚
```bash
# 回滚到上一个版本
git checkout HEAD~1
git push origin main --force
```

### Docker 回滚
```bash
# 使用上一个版本的镜像
docker-compose down
docker tag ai-livestream:previous ai-livestream:latest
docker-compose up -d
```

---

## 紧急联系人

| 角色 | 姓名 | 联系方式 |
|------|------|----------|
| 发布负责人 | - | - |
| 后端开发 | - | - |
| 前端开发 | - | - |
| 运维 | - | - |
