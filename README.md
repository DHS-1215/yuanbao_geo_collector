# Tencent Yuanbao GEO Collector

腾讯元宝 GEO 采集系统，基于 Playwright CDP 实现腾讯元宝网页端自动化采集，支持快速回答 /
专家模式批量任务、回答与信源提取、失败重试、断点续跑、风控识别与恢复、GEO 标准数据包输出，并可直接接入中央 GEO 多平台分析系统。

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
- 支持单任务普通失败自动重试
- 支持 Checkpoint 批次断点续跑
- 程序中断后可自动恢复未完成批次
- 已成功任务自动跳过，失败任务自动补跑
- 支持明确风控状态识别
- 普通失败与风控失败采用不同重试策略
- 风控后采用较长冷却时间，避免短间隔连续请求
- 冷却结束后自动检查页面状态
- 页面异常时支持一次正常刷新恢复
- 页面仍处于风控状态时停止继续请求
- GEO v1 标准 JSONL 输出
- SHA256 完整性校验
- ZIP 标准包生成
- 已通过中央 GEO 系统真实数据校验与正式导入

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

其中：

- `manifest.json`：批次元数据与采集统计
- `tasks.jsonl`：标准任务数据
- `answers.jsonl`：回答及采集状态
- `sources.jsonl`：参考信源数据
- `checksums.json`：标准文件 SHA256 校验值

## 项目结构

```text
yuanbao_geo_collector/
├─ app/
│  ├─ browser/
│  │  └─ cdp.py
│  ├─ core/
│  │  └─ config.py
│  └─ yuanbao/
│     ├─ checkpoint.py
│     ├─ checksum.py
│     ├─ client.py
│     ├─ config.py
│     ├─ exporter.py
│     ├─ extractor.py
│     ├─ geo_contract.py
│     ├─ loader.py
│     ├─ packager.py
│     ├─ result.py
│     ├─ risk_control.py
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

例如 6 个问题会生成：

```text
6 × 2 = 12 个采集任务
```

## 批量采集

正常执行：

```powershell
python -m scripts.smoke_yuanbao_batch
```

如果存在上一次未完成批次，系统会自动恢复该批次。

如需忽略未完成批次并强制创建新批次：

```powershell
python -m scripts.smoke_yuanbao_batch --new-batch
```

批次标准结果输出到：

```text
output/test_batch/
```

Checkpoint 数据保存在：

```text
output/checkpoints/
```

断点恢复时：

```text
成功任务
→ 自动跳过

失败任务
→ 自动重新执行

未完成任务
→ 继续采集
```

批次全部完成后：

```text
active_batch.json
```

会自动清理。

## 普通失败自动重试

普通页面异常、模型菜单瞬时异常、页面元素暂时未加载等问题，会进入普通重试流程。

默认策略：

```text
首次执行
→ 失败
→ 等待 4~8 秒
→ 重试 1

仍失败
→ 等待 4~8 秒
→ 重试 2

仍失败
→ 当前任务记录 failed
→ 后续任务继续执行
```

失败任务仍会保存到 Checkpoint，在后续恢复运行时重新补跑。

## 风控识别与恢复

系统支持识别明确的腾讯元宝风控提示，例如：

```text
访问过于频繁
操作过于频繁
请求过于频繁
请勿频繁操作
检测到异常访问
请完成安全验证
```

风控任务会记录：

```text
acquisition_status = risk_control
```

并与普通失败采用不同处理策略。

默认流程：

```text
检测到风控
→ 不进行短间隔普通重试
→ 进入 60~120 秒冷却
→ 检查页面状态

页面仍存在风控
→ 停止继续请求
→ 保存 risk_control 状态

页面输入区域异常
→ 正常刷新页面一次

页面恢复正常
→ 重新执行当前任务
```

系统不会绕过验证码或规避平台限制，只进行正常页面状态恢复。

## 断点续跑

系统支持程序中断后的批次恢复。

已完成真实 Ctrl+C 中断测试：

```text
TASK 1 成功
TASK 2 成功
TASK 3 执行中 Ctrl+C
→ batch 标记 interrupted
```

重新启动后：

```text
RESUME = YES
TASK 1 自动跳过
TASK 2 自动跳过
TASK 3 重新执行
后续任务继续
```

如果某个任务最终失败：

```text
failed
```

下一次启动时只会重新执行失败任务，其余成功任务自动跳过。

## 生成标准 ZIP

执行：

```powershell
python -m scripts.smoke_yuanbao_package
```

生成：

```text
output/yuanbao_geo_package.zip
```

标准 ZIP 包含且仅包含：

```text
manifest.json
tasks.jsonl
answers.jsonl
sources.jsonl
checksums.json
```

最终真实验收已完成 ZIP 内文件检查与 SHA256 独立复算：

```text
manifest.json   True
tasks.jsonl     True
answers.jsonl   True
sources.jsonl   True
```

## 中央 GEO 系统接入

标准包可直接接入 GEO 多平台分析系统。

进入中央分析系统：

```powershell
cd D:\geo_analysis_system
```

仅校验标准包：

```powershell
python .\scripts\import_platform_package.py `
  --package "D:\yuanbao_geo_collector\output\yuanbao_geo_package.zip" `
  --validate-only
```

正式导入：

```powershell
python .\scripts\import_platform_package.py `
  --package "D:\yuanbao_geo_collector\output\yuanbao_geo_package.zip"
```

最终真实验收批次：

```text
platform=yuanbao
batch=batch_20260910_145315
tasks=12
answers=12
sources=184
metrics=51
```

中央分析系统已完成：

```text
标准包校验
→ 正式导入
→ 数据归档
→ GEO 指标生成
```

归档文件示例：

```text
data/imported/geo_package_yuanbao_batch_20260910_145315.zip
```

## GEO 指标

采集器负责提供原始平台数据，包括：

```text
问题
问题 ID
任务 ID
采集模式
模型
回答正文
采集状态
回答完整状态
信源采集状态
参考信源
批次信息
```

提及率、中正率、负向率等 GEO 指标由中央分析系统统一计算，避免不同采集平台自行维护不同统计口径。

中央系统已完成以下分析验证：

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
- Checkpoint 持久化
- Checkpoint 批次恢复
- 成功任务断点跳过
- 失败任务补跑
- 单任务自动重试
- Runner 异常重试
- 风控文案识别
- 普通失败 / 风控失败分流
- 风控恢复次数限制
- 风控冷却恢复
- 页面关闭处理
- 输入区域恢复
- 页面刷新恢复

执行：

```powershell
pytest -q
```

当前完整测试结果：

```text
62 passed
```

## 最终真实验收

最终完整真实批次：

```text
batch_id=batch_20260910_145315
product=鸿茅药酒

planned_count=12
completed_count=12
success_count=12
failed_count=0

status=completed
sources=184
```

采集器标准包验收：

```text
PACKAGE STATUS: PASS
```

中央 GEO 系统校验：

```text
package validated
platform=yuanbao
batch=batch_20260910_145315
tasks=12
answers=12
sources=184
metrics=0
```

中央 GEO 系统正式导入：

```text
package imported
platform=yuanbao
batch=batch_20260910_145315
tasks=12
answers=12
sources=184
metrics=51
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

当前 Tencent Yuanbao GEO Collector v1 核心开发与真实验收已完成。

完整链路：

```text
腾讯元宝真实网页采集
→ quick / expert 双模式
→ 多问题批量任务
→ 回答正文采集
→ 参考信源提取
→ 普通失败自动重试
→ 风控识别与冷却恢复
→ Checkpoint 断点续跑
→ GEO 标准化
→ SHA256 完整性校验
→ ZIP 标准包
→ 中央 GEO 系统校验
→ 中央 GEO 系统正式导入
→ GEO 指标生成
→ 提及率 / 中正率 / 负向率分析
→ 信源分析
```

当前状态：

```text
核心功能完成
真实批量采集通过
断点续跑验证通过
普通失败重试验证通过
风控恢复逻辑验证通过
标准数据包验证通过
中央 GEO 分析系统接入通过
62 项自动测试通过
```