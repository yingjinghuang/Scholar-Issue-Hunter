# 🔬 Scholar Issue Hunter

**Scholar Issue Hunter** is a fully automated, GitHub-powered dashboard that tracks open "Call for Papers" (Special Issues) from top academic journals.

It eliminates the need to manually check journal websites. This system runs automatically in the cloud via **GitHub Actions**, scrapes the latest data, bypasses anti-bot protections, and publishes a beautiful dashboard to **GitHub Pages**.

**[🔴 Live Demo](https://yingjinghuang.github.io/Scholar-Issue-Hunter/)**

## ✨ Features

* **☁️ Zero Server Cost**: Runs entirely on GitHub Actions (Free Tier).
* **🛡️ Anti-Ban Capable**: Integrated with **ScraperAPI** to bypass 403 Forbidden/Cloudflare protections on ScienceDirect.
* **🌍 Multi-Language**: Built-in "AI Summary" feature to translate journal descriptions into Chinese/Japanese/Korean/Spanish on demand.
* **🧠 Smart Parsing**: Handles complex page layouts (e.g., nested `div` structures in *Cities* vs. standard layouts in *RSE*).
* **📱 Modern UI**: Responsive design with journal filtering, search, and collapsible headers.

---

## 🚀 Deployment Guide (How to use this)

You don't need to write code or install Python locally. Just follow these steps to get your own tracker running.

### Step 1: Fork this Repository

Click the **Fork** button at the top right of this page to copy this project to your own GitHub account.

### Step 2: Get a ScraperAPI Key

The scraper needs a proxy service to bypass Elsevier's firewalls.

1. Go to [ScraperAPI](https://www.scraperapi.com/).
2. Sign up for a free account (The free tier gives 1,000 credits/month, which is enough for daily updates).
3. Copy your **API Key** from the dashboard.

### Step 3: Configure GitHub Secrets

To secure your API Key, we store it in GitHub Secrets.

1. Go to your forked repository's **Settings** tab.
2. On the left sidebar, click **Secrets and variables** > **Actions**.
3. Click the **New repository secret** button.
4. **Name**: `SCRAPER_API_KEY`
5. **Secret**: Paste your ScraperAPI Key here.
6. Click **Add secret**.

### Step 4: Enable GitHub Actions

Since this is a forked repo, workflows might be disabled by default.

1. Go to the **Actions** tab.
2. Click the green button **I understand my workflows, go ahead and enable them**.
3. (Optional) To trigger the first run immediately: Select **"Auto Scrape Issues"** on the left -> Click **Run workflow**.

### Step 5: Setup GitHub Pages

This turns the data into a website.

1. Go to the **Settings** tab.
2. On the left sidebar, click **Pages**.
3. Under **Build and deployment** > **Source**, select **Deploy from a branch**.
4. **Branch**: Select `main` (or `master`) and folder `/ (root)`.
5. Click **Save**.

⏳ **Wait a few minutes.** After the Action finishes running (check the "Actions" tab), refresh the Pages settings. You will see a link like `https://yourname.github.io/scholar-issue-hunter/`. **Click it, and your site is live!**

---

## ⚙️ Configuration

### Adding New Journals

To track more journals, simply edit the `journals.json` file in your repository (you can edit it directly on GitHub website).

**Format:**

```json
{
  "name": "Journal Name",
  "url": "https://www.sciencedirect.com/journal/.../about/call-for-papers",
  "image": "assets/images/journal-cover.jpg"
}

```

*Note: If you add a new journal, make sure to upload a cover image to `assets/images/` folder as well.*

### Changing Update Frequency

The scraper runs daily by default. To change this, edit `.github/workflows/scrape.yml`:

```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # Runs at 00:00 UTC every day

```

---

## 💻 For Developers (Advanced)

If you want to modify the scraping logic or add a journal with a completely unique layout, you can debug locally.

**Requirements:** `pip install requests beautifulsoup4`

**Testing Rules (Offline Mode):**
Use this to test parsing logic without consuming API credits.

1. Save the target webpage as an `.html` file.
2. Run the local debugger:
```bash
python scripts/scraper_local.py

```



**Structure:**

* `scripts/scraper.py`: Main logic, handles network and file saving.
* `scripts/parsers.py`: **Strategy Pattern**. Contains specific parsing rules for different journal layouts (e.g., `parse_cities_sciencedirect` vs `parse_rse_sciencedirect`).

---

## 📄 License

MIT License.

**Disclaimer**: This tool is for personal and educational research purposes only. Please verify all deadlines on the official journal websites.