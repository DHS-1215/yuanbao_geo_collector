# Tencent Yuanbao GEO Collector

腾讯元宝 GEO 采集系统，基于 Playwright CDP 实现腾讯元宝网页端自动化采集，支持快速回答 / 专家模式批量任务、回答与信源提取、GEO 标准数据包输出，并可接入中央 GEO 多平台分析系统。

## 功能特性

- 基于 Playwright CDP 连接已登录的 Chrome
- 自动识别腾讯元宝页面，避免误选 `chrome://downloads`
- 支持快速回答（quick）
- 支持专家模式（expert）
- 支持多问题批量采集
- 单问题自动展开 quick / expert 双模式任务
- 自动新建会话，隔离不同任务上下文
- 支持部分澄清卡片自动跳过
- 采集回答正文
- 采集参考信源
- 回答状态与信源采集状态独立记录
- Question / Task / Answer / Source 稳定 ID
- GEO v1 标准 JSONL 输出
- SHA256 完整性校验
- ZIP 标准包生成
- 已通过中央 GEO 系统真实数据接入验证

## GEO 标准输出

每个批次输出以下 5 个标准文件：

```text
manifest.json
tasks.jsonl
answers.jsonl
sources.jsonl
checksums.json
```

可进一步打包为：

```text
yuanbao_geo_package.zip
```

## 项目结构

```text
yuanbao_geo_collector/
├─ app/
│  ├─ browser/
│  │  └─ cdp.py
│  ├─ core/
│  │  └─ config.py
│  └─ yuanbao/
│     ├─ checksum.py
│     ├─ client.py
│     ├─ exporter.py
│     ├─ extractor.py
│     ├─ geo_contract.py
│     ├─ loader.py
│     ├─ packager.py
│     ├─ result.py
│     ├─ runner.py
│     ├─ source.py
│     └─ types.py
├─ input/
│  └─ questions.csv
├─ scripts/
├─ tests/
├─ .gitignore
├─ README.md
└─ requirements.txt
```

## 环境要求

推荐环境：

```text
Python 3.11+
Google Chrome
Playwright
```

创建虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

安装依赖：

```powershell
pip install -r requirements.txt
```

## 启动 Chrome CDP

执行：

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --remote-debugging-port=9222 `
  --user-data-dir="D:\yuanbao_geo_collector\.chrome-profile"
```

首次使用需要在该 Chrome Profile 中登录腾讯元宝。

默认 CDP 地址：

```text
http://127.0.0.1:9222
```

## 准备采集问题

编辑：

```text
input/questions.csv
```

示例：

```csv
id,question
001,鸿茅药酒是正规药品吗？
002,鸿茅药酒有什么功效？
003,鸿茅药酒适合哪些人群？
```

每个问题默认生成两个 GEO 任务：

```text
quick
expert
```

## 批量采集

执行：

```powershell
python -m scripts.smoke_yuanbao_batch
```

批次结果输出到：

```text
output/test_batch/
```

## 生成标准 ZIP

执行：

```powershell
python -m scripts.smoke_yuanbao_package
```

生成：

```text
output/yuanbao_geo_package.zip
```

标准 ZIP 包含：

```text
manifest.json
tasks.jsonl
answers.jsonl
sources.jsonl
checksums.json
```

## 中央 GEO 系统接入

标准包可直接接入 GEO 多平台分析系统。

校验示例：

```powershell
python .\scripts\import_platform_package.py `
  --package D:\yuanbao_geo_collector\output\yuanbao_geo_package.zip `
  --validate-only
```

真实环境已完成以下验证：

```text
platform=yuanbao
tasks=12
answers=12
sources=181
```

标准包可被中央系统正确识别和导入。

## GEO 指标

采集器负责提供原始平台数据，包括：

```text
问题
采集模式
回答正文
采集状态
参考信源
```

提及率、中正率、负向率等 GEO 指标由中央分析系统统一计算，避免不同采集平台自行维护不同统计口径。

真实批次已完成中央分析验证，包括：

- 提及率
- 中正率
- 负向率
- quick / expert 模式对比
- 问题级明细
- 信源引用统计
- 唯一参考文献统计
- Top10 信源覆盖分析

## 测试

项目当前测试覆盖：

- CDP 页面选择
- GEO 协议常量
- 稳定 ID
- Question / Task 身份
- quick / expert 双模式任务
- 回答采集状态
- 信源采集状态
- tasks.jsonl
- answers.jsonl
- sources.jsonl
- manifest.json
- SHA256 checksum
- ZIP 标准包
- Batch 时间范围

执行：

```powershell
pytest -q
```

当前核心测试已通过：

```text
44 passed
```

## 安全说明

以下内容不会提交到 Git：

```text
.env
.venv/
.chrome-profile/
output/
__pycache__/
.pytest_cache/
.idea/
```

请勿将登录态、Cookie、真实业务采集数据或敏感配置提交到公开仓库。

## 项目状态

当前已完成：

```text
腾讯元宝真实网页采集
→ quick / expert 双模式
→ 批量任务
→ 回答与信源提取
→ GEO 标准化
→ SHA256 校验
→ ZIP 打包
→ 中央 GEO 系统接入
→ 提及率 / 中正率 / 负向率分析
→ 信源分析
```
