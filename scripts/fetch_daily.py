import os
#!/usr/bin/env python3
"""
fetch_daily.py
Fetches real daily data from free, no-auth APIs and writes them to data/.
Runs inside GitHub Actions every day.

Data collected:
  - Astronomy Picture of the Day (NASA APOD)
  - Trending GitHub repos (Python)
  - A programming quote
  - Bitcoin & Ethereum price snapshot
  - Random fun fact
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def fetch(url: str, headers: dict = {}) -> dict | list | None:
    req = urllib.request.Request(url, headers={"User-Agent": "daily-pulse-bot/1.0", **headers})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  ⚠  Could not fetch {url}: {e}")
        return None


# ── 1. NASA Astronomy Picture of the Day ─────────────────────────────────────
print("🔭  Fetching NASA APOD...")
apod = fetch("https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY")
apod_data = {
    "date": apod.get("date"),
    "title": apod.get("title"),
    "explanation": apod.get("explanation", "")[:400] + "…",
    "url": apod.get("url"),
    "media_type": apod.get("media_type"),
} if apod else {"error": "unavailable"}

# ── 2. Trending GitHub repos (via public search API) ─────────────────────────
print("📈  Fetching trending GitHub repos...")
gh = fetch(
    "https://api.github.com/search/repositories"
    "?q=created:%3E2024-01-01+stars:%3E500&sort=stars&order=desc&per_page=5"
)
trending = []
if gh and "items" in gh:
    for r in gh["items"][:5]:
        trending.append({
            "name": r["full_name"],
            "description": (r.get("description") or "")[:120],
            "stars": r["stargazers_count"],
            "language": r.get("language"),
            "url": r["html_url"],
        })

# ── 3. Programming quote (quotable.io) ───────────────────────────────────────
print("💬  Fetching quote...")
q = fetch("https://zenquotes.io/api/random")
quote_data = {"text": q[0]["q"], "author": q[0]["a"]} if q and isinstance(q, list) else {
    "text": "Programs must be written for people to read, and only incidentally for machines to execute.",
    "author": "Harold Abelson"
}

# ── 4. Crypto price snapshot (CoinGecko – no auth required) ──────────────────
print("₿   Fetching crypto prices...")
crypto_raw = fetch(
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=bitcoin,ethereum,solana&vs_currencies=usd&include_24hr_change=true"
)
crypto = {}
if crypto_raw:
    for coin, vals in crypto_raw.items():
        crypto[coin] = {
            "usd": vals.get("usd"),
            "change_24h": round(vals.get("usd_24h_change", 0), 2),
        }

# ── 5. Fun fact (uselessfacts API) ───────────────────────────────────────────
print("🎲  Fetching fun fact...")
fact_raw = fetch("https://uselessfacts.jsph.pl/api/v2/facts/random?language=en")
fun_fact = fact_raw.get("text", "The word 'nerd' was first coined by Dr. Seuss in 1950.") if fact_raw else ""

# ── Assemble & write ──────────────────────────────────────────────────────────
payload = {
    "fetched_at": TIMESTAMP,
    "astronomy_picture_of_the_day": apod_data,
    "trending_github_repos": trending,
    "quote_of_the_day": quote_data,
    "crypto_prices": crypto,
    "fun_fact": fun_fact,
}

out_path = f"data/{TODAY}.json"
os.makedirs("data", exist_ok=True)
with open(out_path, "w") as f:
    json.dump(payload, f, indent=2, ensure_ascii=False)
print(f"✅  Wrote {out_path}")

# ── Update README summary ─────────────────────────────────────────────────────
readme = f"""# 🌍 Daily Pulse

> Auto-updated every day at 07:00 UTC via GitHub Actions. No manual work needed.

## 📅 Latest snapshot — {TODAY}

### 🔭 NASA Astronomy Picture of the Day
**{apod_data.get('title', 'N/A')}**
{apod_data.get('explanation', '')}
[View full image →]({apod_data.get('url', '#')})

---

### 💬 Quote of the Day
> *"{quote_data['text']}"*
> — {quote_data['author']}

---

### ₿ Crypto Snapshot
| Coin | Price (USD) | 24h Change |
|------|------------|-----------|
"""
for coin, vals in crypto.items():
    change = vals.get('change_24h', 0)
    arrow = "🟢" if change >= 0 else "🔴"
    readme += f"| {coin.capitalize()} | ${vals.get('usd', 'N/A'):,} | {arrow} {change:+.2f}% |\n"

readme += f"""
---

### 📈 Trending GitHub Repos
| Repo | Language | ⭐ Stars |
|------|----------|---------|
"""
for r in trending:
    readme += f"| [{r['name']}]({r['url']}) | {r.get('language') or '—'} | {r['stars']:,} |\n"

readme += f"""
---

### 🎲 Fun Fact
{fun_fact}

---

*Last updated: {TIMESTAMP} · [See all daily snapshots](data/)*
"""

with open("README.md", "w") as f:
    f.write(readme)
print("✅  README.md updated")