# 🔬 学术特刊猎手 (Scholar Issue Hunter)

**Scholar Issue Hunter** 是一个全自动化的工具，旨在追踪顶级学术期刊最新的“征稿启事”（Call for Papers / Special Issues）。

它解决了科研人员需要手动反复检查多个期刊网站确认截止日期的痛点。该系统完全运行在 **GitHub Actions** 云端，自动抓取数据，利用 **ScraperAPI** 绕过复杂的反爬机制，最终生成一个美观、可搜索、支持翻译的 **GitHub Pages** 仪表盘。

**[🔴 在线演示](https://yingjinghuang.github.io/Scholar-Issue-Hunter/)**


## 📚 支持的期刊

目前，该猎手追踪以下 ScienceDirect (Elsevier) 旗下的期刊：

| 期刊名称 | 缩写 | 领域 |
| --- | --- | --- |
| **Remote Sensing of Environment** | RSE | 遥感、地球科学 |
| **Cities** | - | 城市研究、规划 |
| **Building and Environment** | BAE | 土木工程、建筑环境 |
| **Computers, Environment and Urban Systems** | CEUS | GIS、城市信息学 |

> *可以通过修改配置文件轻松添加更多期刊。*

---

## ✨ 功能亮点

* **☁️ 零服务器成本**：完全运行在 GitHub Actions 上（使用免费额度）。
* **🛡️ 强力抗反爬**：集成 **ScraperAPI**，轻松穿透 Elsevier 的防火墙（403 Forbidden / Cloudflare 盾）。
* **🧠 智能解析引擎**：
* 采用**策略模式** (`parsers.py`) 处理不同期刊的网页排版（例如 *Cities* 复杂的嵌套结构 vs *RSE* 的标准结构）。
* **原子化扫描**：无论 DOM 藏得有多深，都能精准提取截止日期、编辑名单和简介。
* **数据清洗**：自动剔除冗余的头衔（Dr./Prof.）、邮箱和单位信息，保持界面清爽。


* **🌍 多语言支持**：内置“AI 摘要”功能，点击详情即可按需将英文简介翻译成中文/日文/韩文等。
* **💻 现代化前端**：
* **期刊筛选**：可查看所有内容或只看特定期刊。
* **实时搜索**：支持按关键词过滤（如 "AI", "Climate"）。
* **交互设计**：支持折叠/展开标题栏，卡片式布局。



---

## 🚀 部署指南 (如何拥有你自己的猎手)

你不需要懂 Python 编程，也不需要在本地安装任何东西。只需按照以下步骤操作：

### 第一步：Fork 本仓库

点击页面右上角的 **Fork** 按钮，将本项目复制到你自己的 GitHub 账号下。

### 第二步：获取 ScraperAPI Key

爬虫需要代理服务来绕过期刊网站的防火墙。

1. 前往 [ScraperAPI](https://www.scraperapi.com/)。
2. 注册一个免费账号（免费版提供 1,000 次请求/月，对于每日更新完全够用）。
3. 复制仪表盘上的 **API Key**。

### 第三步：配置 GitHub Secrets

为了安全起见，我们将 Key 存储在仓库的密钥中。

1. 进入你 Fork 后的仓库，点击 **Settings** (设置) 选项卡。
2. 在左侧栏点击 **Secrets and variables** > **Actions**。
3. 点击 **New repository secret** 按钮。
4. **Name**: `SCRAPER_API_KEY`
5. **Secret**: 粘贴你的 ScraperAPI Key。
6. 点击 **Add secret**。

### 第四步：启用 GitHub Actions

因为是 Fork 的项目，自动任务默认可能是关闭的。

1. 点击 **Actions** 选项卡。
2. 点击绿色的 **I understand my workflows, go ahead and enable them** 按钮。
3. (可选) 立即触发第一次运行：在左侧选择 **"Auto Scrape Issues"** -> 点击 **Run workflow**。

### 第五步：开启 GitHub Pages

这一步将生成的 JSON 数据渲染成网页。

1. 点击 **Settings** 选项卡。
2. 在左侧栏点击 **Pages**。
3. 在 **Build and deployment** > **Source** 下，选择 **Deploy from a branch**。
4. **Branch**: 选择 `main` (或 `master`) 分支，文件夹选择 `/ (root)`。
5. 点击 **Save**。

⏳ **稍等几分钟。** 等待 Actions 跑完（检查 Actions 标签页全是绿色对号），刷新 Pages 设置页面，你会看到一个链接，例如 `https://你的名字.github.io/scholar-issue-hunter/`。**点击它，你的专属学术追踪站就上线了！**

---

## ⚙️ 配置说明

### 添加新期刊

要追踪更多期刊，只需编辑仓库中的 `journals.json` 文件（可以直接在 GitHub 网页上编辑）。

**格式：**

```json
{
  "name": "期刊名称",
  "url": "https://www.sciencedirect.com/journal/.../about/call-for-papers",
  "image": "assets/images/journal-cover.jpg"
}

```

*注意：添加新期刊后，记得找一张该期刊的封面图上传到 `assets/images/` 文件夹。*

### 修改更新频率

爬虫默认每天运行一次。如需修改，请编辑 `.github/workflows/scrape.yml`：

```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # 每天 UTC 时间 00:00 (北京时间早 8:00) 运行

```

---

## 💻 开发者指南 (高阶)

如果你想修改爬取逻辑，或者遇到了排版非常奇特的期刊需要调试，可以使用本地开发模式。

**依赖环境：** `pip install requests beautifulsoup4`

### 1. 测试解析规则 (离线调试模式)

使用此模式可以在不消耗 API 额度的情况下测试解析逻辑。

1. 手动将目标期刊的网页保存为 `.html` 文件（例如存放在 `test_data/` 目录）。
2. 运行本地调试脚本：
```bash
# 请先修改脚本最后几行，指向你的 html 文件路径
python scripts/scraper_local.py

```



### 2. 运行完整爬虫 (生产模式)

在本地运行全量抓取并生成 `data/issues.json`：

```bash
# Windows (PowerShell)
$env:SCRAPER_API_KEY="你的_API_KEY"
python scripts/scraper.py

# Mac/Linux
export SCRAPER_API_KEY="你的_API_KEY"
python scripts/scraper.py

```

**项目结构：**

* `scripts/scraper.py`: 主程序，负责网络请求、文件读写和循环调度。
* `scripts/parsers.py`: **策略模式核心**。存放针对不同期刊布局的解析函数（例如 `parse_cities_sciencedirect` 和 `parse_rse_sciencedirect`）。

---

## 📄 许可证

本项目采用 MIT 许可证开源。

**免责声明**：本工具仅供个人学术研究和学习使用。请遵守目标网站的 robots.txt 协议及服务条款。请务必以期刊官方网站上的截止日期为准。