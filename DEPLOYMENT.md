# 🚀 快速部署指南 / Quick Deployment Guide

## 中文说明

### 第一步：上传到 GitHub

1. 在 GitHub 上创建新仓库（例如：`journal-tracker`）
2. 将所有文件上传到仓库根目录
3. 确保包含所有文件（包括 `.github` 文件夹）

### 第二步：启用 GitHub Pages

1. 进入仓库 Settings（设置）
2. 点击左侧菜单的 "Pages"
3. 在 "Source" 下拉菜单选择 `main` 分支
4. 选择 `/` (root) 目录
5. 点击 "Save" 保存
6. 等待 2-3 分钟

### 第三步：启用 GitHub Actions

1. 点击仓库顶部的 "Actions" 标签
2. 如果看到提示，点击 "I understand my workflows, go ahead and enable them"
3. 点击左侧的 "Update Special Issues Data"
4. 点击 "Run workflow" → "Run workflow" 手动运行一次

### 第四步：访问网站

访问：`https://[你的GitHub用户名].github.io/[仓库名]/`

例如：`https://username.github.io/journal-tracker/`

---

## English Instructions

### Step 1: Upload to GitHub

1. Create a new repository on GitHub (e.g., `journal-tracker`)
2. Upload all files to the repository root
3. Ensure all files are included (including `.github` folder)

### Step 2: Enable GitHub Pages

1. Go to repository Settings
2. Click "Pages" in the left menu
3. Under "Source" dropdown, select `main` branch
4. Select `/` (root) directory
5. Click "Save"
6. Wait 2-3 minutes

### Step 3: Enable GitHub Actions

1. Click "Actions" tab at the top
2. If prompted, click "I understand my workflows, go ahead and enable them"
3. Click "Update Special Issues Data" on the left
4. Click "Run workflow" → "Run workflow" to run manually

### Step 4: Access Your Site

Visit: `https://[your-GitHub-username].github.io/[repository-name]/`

Example: `https://username.github.io/journal-tracker/`

---

## 📋 文件清单 / File Checklist

- ✅ `index.html` - 主页面 / Main page
- ✅ `scraper.py` - 爬虫脚本 / Scraper script
- ✅ `requirements.txt` - Python 依赖 / Python dependencies
- ✅ `README.md` - 项目说明 / Project documentation
- ✅ `.github/workflows/update-data.yml` - 自动化工作流 / Automation workflow
- ✅ `data/special_issues.json` - 数据文件 / Data file
- ✅ `.gitignore` - Git 忽略文件 / Git ignore file

---

## ⚙️ 配置选项 / Configuration Options

### 修改更新频率 / Change Update Frequency

编辑 `.github/workflows/update-data.yml`:

```yaml
schedule:
  - cron: '0 8 * * *'  # 每天 8:00 UTC / Daily at 8:00 UTC
  # - cron: '0 */12 * * *'  # 每 12 小时 / Every 12 hours
  # - cron: '0 0 * * 0'  # 每周日 / Every Sunday
```

### 添加期刊 / Add Journals

编辑 `scraper.py` 中的 `journals` 列表 / Edit `journals` list in `scraper.py`:

```python
self.journals = [
    {
        'name': 'Your Journal Name',
        'url': 'https://journal-url.com/special-issues',
        'type': 'elsevier'
    }
]
```

---

## 🆘 常见问题 / FAQ

### Q: 为什么看不到特刊数据？
**A:** 
1. 检查 GitHub Actions 是否运行成功
2. 查看 `data/special_issues.json` 是否存在
3. 等待几分钟让 GitHub Pages 更新

### Q: Why can't I see special issues data?
**A:**
1. Check if GitHub Actions ran successfully
2. Verify `data/special_issues.json` exists
3. Wait a few minutes for GitHub Pages to update

### Q: 如何手动更新数据？
**A:** Actions → Update Special Issues Data → Run workflow

### Q: How to manually update data?
**A:** Actions → Update Special Issues Data → Run workflow

---

## 📞 获取帮助 / Get Help

- 查看详细文档：`README.md`
- 提交问题：GitHub Issues
- 检查日志：Actions 标签 → 最近的运行记录

- Read full documentation: `README.md`
- Report issues: GitHub Issues
- Check logs: Actions tab → Recent workflow runs

---

**祝使用愉快！ / Enjoy!** 🎉
