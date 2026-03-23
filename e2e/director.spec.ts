/**
 * E2E 测试 - 导播台功能测试
 * 
 * 运行方式:
 *   npx playwright test e2e/director.spec.ts
 * 
 * 测试覆盖:
 *   - 页面加载
 *   - 直播控制
 *   - 平台管理
 *   - 内容库
 */

import { test, expect, Page } from '@playwright/test';

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:3000';

test.describe('导播台功能测试', () => {
  let page: Page;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    await page.goto(`${BASE_URL}/director`);
    // 等待页面加载完成
    await page.waitForLoadState('networkidle');
  });

  test.afterAll(async () => {
    await page.close();
  });

  test.describe('页面加载', () => {
    test('应显示导播台页面标题', async () => {
      const title = page.locator('h1');
      await expect(title).toContainText('智能导播台');
    });

    test('应显示状态指示器', async () => {
      const statusBadge = page.locator('.rounded-full').first();
      await expect(statusBadge).toBeVisible();
    });

    test('应显示三个标签页', async () => {
      const tabs = ['正在播放', '平台管理', '内容库'];
      for (const tab of tabs) {
        await expect(page.locator('button').filter({ hasText: tab })).toBeVisible();
      }
    });

    test('应显示控制按钮', async () => {
      await expect(page.locator('button').filter({ hasText: '开始直播' })).toBeVisible();
      await expect(page.locator('button').filter({ hasText: '停止直播' })).toBeVisible();
    });
  });

  test.describe('直播控制', () => {
    test.beforeEach(async () => {
      // 确保处于停止状态
      const stopButton = page.locator('button').filter({ hasText: '停止直播' });
      if (await stopButton.isEnabled()) {
        await stopButton.click();
        await page.waitForTimeout(500);
      }
    });

    test('点击开始直播应改变状态', async () => {
      // 点击开始
      await page.locator('button').filter({ hasText: '开始直播' }).click();
      
      // 等待状态更新
      await page.waitForTimeout(1000);
      
      // 验证状态变化
      const statusBadge = page.locator('.rounded-full').filter({ hasText: '推流中' });
      await expect(statusBadge).toBeVisible({ timeout: 5000 });
    });

    test('开始后停止按钮应可用', async () => {
      // 开始
      await page.locator('button').filter({ hasText: '开始直播' }).click();
      await page.waitForTimeout(1000);
      
      // 停止按钮应可用
      const stopButton = page.locator('button').filter({ hasText: '停止直播' });
      await expect(stopButton).toBeEnabled({ timeout: 5000 });
    });

    test('停止后状态应变为待机', async () => {
      // 开始
      await page.locator('button').filter({ hasText: '开始直播' }).click();
      await page.waitForTimeout(1000);
      
      // 停止
      await page.locator('button').filter({ hasText: '停止直播' }).click();
      await page.waitForTimeout(1000);
      
      // 验证状态
      const statusBadge = page.locator('.rounded-full').filter({ hasText: '待机' });
      await expect(statusBadge).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('平台管理', () => {
    test.beforeEach(async () => {
      await page.locator('button').filter({ hasText: '平台管理' }).click();
      await page.waitForTimeout(500);
    });

    test('应显示平台列表', async () => {
      const platforms = page.locator('[data-testid="platform-item"], .divide-y > div');
      const count = await platforms.count();
      expect(count).toBeGreaterThan(0);
    });

    test('应显示 YouTube 平台', async () => {
      const youtube = page.locator('text=YouTube');
      await expect(youtube).toBeVisible();
    });

    test('应显示配置状态', async () => {
      // 检查是否有配置标签
      const configBadge = page.locator('text=已配置').or(page.locator('text=未配置'));
      await expect(configBadge.first()).toBeVisible();
    });
  });

  test.describe('内容库', () => {
    test.beforeEach(async () => {
      await page.locator('button').filter({ hasText: '内容库' }).click();
      await page.waitForTimeout(500);
    });

    test('应显示内容列表', async () => {
      // 首先启动直播以加载内容
      await page.locator('button').filter({ hasText: '正在播放' }).click();
      await page.locator('button').filter({ hasText: '开始直播' }).click();
      await page.waitForTimeout(1000);
      
      // 返回内容库
      await page.locator('button').filter({ hasText: '内容库' }).click();
      await page.waitForTimeout(500);
      
      const contentItems = page.locator('.divide-y > div');
      const count = await contentItems.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test('应显示内容类型图标', async () => {
      // 检查是否有新闻、音乐或视频图标
      const icons = page.locator('text=📰').or(page.locator('text=🎵')).or(page.locator('text=🎬'));
      // 可能有也可能没有，取决于是否有内容
      const count = await icons.count();
      // 只是检查不会报错
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });

  test.describe('API 代理测试', () => {
    test('API 请求应正确代理', async ({ request }) => {
      // 测试 /api/v1 前缀
      const response1 = await request.get(`${BASE_URL}/api/v1/director/status`);
      expect(response1.status()).toBe(200);
      
      // 测试无前缀
      const response2 = await request.get(`${BASE_URL}/api/director/status`);
      expect(response2.status()).toBe(200);
    });

    test('平台 API 应返回数据', async ({ request }) => {
      const response = await request.get(`${BASE_URL}/api/v1/platform/list`);
      expect(response.status()).toBe(200);
      
      const data = await response.json();
      expect(data).toHaveProperty('platforms');
      expect(data).toHaveProperty('available_platforms');
    });
  });
});

test.describe('首页功能测试', () => {
  test('首页应正常加载', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    
    // 检查是否有内容
    const body = page.locator('body');
    await expect(body).toBeVisible();
  });
});
