# VC 信息每日推送

自动抓取 VC/科技圈博客与 Newsletter，调用 Gemini AI 生成中文摘要和核心观点，通过 Telegram Bot 每日推送。

## 功能

- 支持 RSS/Atom 和纯 HTML 两种抓取方式
- 自动去重，已推送的文章不重复发送
- 调用 `gemini-3-flash-preview` 生成中文摘要和核心观点
- 无 Gemini Key 时自动降级，照常推送原始摘要
- P1 源全量推送，P2 源每次最多推送 2 篇
- 消息超长时自动分段发送

## 项目结构

```
messge_push/
├── main.py            # 主入口：抓取 → AI 处理 → 推送
├── fetchers.py        # 文章抓取逻辑（RSS + 特殊爬虫）
├── notifier.py        # Telegram 消息格式化与发送
├── ai_processor.py    # Gemini AI 摘要生成
├── config.py          # 配置加载（.env + CSV）
├── state.py           # 已推送记录（去重）
├── requirements.txt
├── .env.example
└── vc信息源收集_数据表_表格.csv   # 信息源列表
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填入：

```
TELEGRAM_BOT_TOKEN=你的 Bot Token
TELEGRAM_CHAT_ID=你的 Chat ID
GEMINI_API_KEY=你的 Gemini API Key（可选）
```

### 3. 运行

```bash
python main.py
```

### 4. 定时运行（macOS）

使用项目内附带的 `com.user.vc_push.plist` 配置 launchd，每天定时执行：

```bash
cp com.user.vc_push.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.user.vc_push.plist
```

## Telegram 消息格式

```
🔴 [P1] a16z

📌 <文章标题>
🔗 https://...
📝 LLM 正在被用于评估代码质量，作者构建了一个专门的基准测试工具...
💡 核心观点：
- LLM 在游戏逻辑实现上表现出明显差异
- GPT-4o 在速度上优于 Claude，但准确性较低
- 基准测试覆盖了 10 种主流模型
```

无 Gemini Key 时退回显示原始摘要。

## 信息源管理

信息源配置在 `vc信息源收集_数据表_表格.csv`，字段格式：

```
名称, 类型, URL, 备注, 空, 优先级(P1/P2)
```

### 添加 RSS 源

1. 在 `fetchers.py` 的 `RSS_MAP` 中添加：
   ```python
   "domain.com": "https://domain.com/feed",
   ```
2. 在 CSV 末尾添加一行，优先级填 `P1` 或 `P2`

### 添加无 RSS 的网站

1. 在 `fetchers.py` 中参考 `fetch_paul_graham()` 新增抓取函数
2. 在 `get_articles()` 的"特殊抓取"区域添加判断：
   ```python
   if "domain.com" in domain:
       return fetch_xxx()
   ```
3. 在 CSV 中添加对应行

## 当前信息源

| 名称 | 优先级 | 类型 |
|------|--------|------|
| a16z | P1 | RSS |
| Ben Thompson (Stratechery) | P1 | RSS |
| ben-evans | P1 | RSS |
| Elad Gil | P1 | RSS |
| paulgraham | P1 | HTML |
| Tomasz Tunguz | P1 | RSS |
| ark-invest | P1 | HTML |
| coatue | P1 | HTML |
| lex fridman | P1 | YouTube RSS |
| Invest Like The Best | P1 | RSS |
| First Round Review | P2 | HTML |
| Superscout | P2 | HTML |
| Lenny's Newsletter | P2 | RSS |
| avc | P2 | RSS |
| Homebrew 合伙人 | P2 | RSS |
| latent.space | P2 | RSS |
| techmeme | P2 | RSS |
| bensbites | P2 | RSS |
| generalist | P2 | RSS |
| everyto | P2 | RSS |
| strictlyvc | P2 | RSS |
