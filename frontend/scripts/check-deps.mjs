#!/usr/bin/env node
/**
 * 依赖版本兼容性检查脚本
 * 避免版本不匹配问题
 */

import { readFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const rootDir = join(__dirname, '..');

let hasErrors = false;

console.log('🔍 依赖兼容性检查...\n');

// 1. 检查 Tailwind CSS 版本
function checkTailwind() {
  const pkgPath = join(rootDir, 'package.json');
  const cssPath = join(rootDir, 'src/app/globals.css');

  if (!existsSync(pkgPath) || !existsSync(cssPath)) {
    console.log('⚠️  跳过 Tailwind 检查 (文件不存在)');
    return;
  }

  const pkg = JSON.parse(readFileSync(pkgPath, 'utf-8'));
  const css = readFileSync(cssPath, 'utf-8');

  // 获取 Tailwind 版本
  const tailwindDeps = pkg.devDependencies?.tailwindcss || pkg.dependencies?.tailwindcss;
  if (!tailwindDeps) {
    console.log('⚠️  Tailwind CSS 未安装');
    return;
  }

  const isV4 = tailwindDeps.startsWith('^4') || tailwindDeps.startsWith('4');
  const usesV4Syntax = css.includes('@import "tailwindcss"');

  if (isV4 && !usesV4Syntax) {
    console.log('❌ Tailwind CSS v4 已安装，但使用 v3 语法');
    console.log('   建议: 使用 @import "tailwindcss"; 语法');
    hasErrors = true;
  } else if (!isV4 && usesV4Syntax) {
    console.log('❌ Tailwind CSS v3 已安装，但使用 v4 语法');
    console.log('   建议: 使用 @tailwind base; @tailwind components; @tailwind utilities; 语法');
    hasErrors = true;
  } else {
    console.log('✅ Tailwind CSS 版本与语法匹配');
    console.log(`   版本: ${tailwindDeps}`);
    console.log(`   语法: ${isV4 ? 'v4 (@import)' : 'v3 (@tailwind)'}`);
  }
}

// 2. 检查必要文件
function checkRequiredFiles() {
  const requiredFiles = [
    'package.json',
    'tsconfig.json',
    'next.config.ts',
    'tailwind.config.ts',
    'postcss.config.mjs',
    'src/app/globals.css',
    'src/app/layout.tsx',
    'src/app/page.tsx',
  ];

  console.log('\n📁 检查必要文件...');
  for (const file of requiredFiles) {
    const path = join(rootDir, file);
    if (existsSync(path)) {
      console.log(`   ✅ ${file}`);
    } else {
      console.log(`   ❌ ${file} 不存在`);
      hasErrors = true;
    }
  }
}

// 3. 检查 Node 版本
function checkNodeVersion() {
  const requiredVersion = 18;
  const currentVersion = parseInt(process.version.slice(1).split('.')[0]);

  console.log('\n📋 Node.js 版本检查...');
  if (currentVersion >= requiredVersion) {
    console.log(`   ✅ Node.js ${process.version} (需要 >= ${requiredVersion})`);
  } else {
    console.log(`   ❌ Node.js ${process.version} (需要 >= ${requiredVersion})`);
    hasErrors = true;
  }
}

// 执行检查
checkTailwind();
checkRequiredFiles();
checkNodeVersion();

console.log('\n' + '='.repeat(50));

if (hasErrors) {
  console.log('❌ 检查发现问题，请修复后再启动');
  process.exit(1);
} else {
  console.log('✅ 所有检查通过');
  process.exit(0);
}
