#!/usr/bin/env python3
"""
randomizer.py
The brain of Daily Pulse. Runs every hour and decides:
  - Should today be a skip day? (~25% of days get skipped entirely)
  - How many commits should happen today? (1–10, weighted to feel natural)
  - Which hours should commits happen in? (spread like a real dev's day)
  - What should the commit message say? (varied, realistic messages)

Stores state in logs/schedule.json so all 24 hourly runs share the same plan.
"""

import os
import json
import random
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Seed randomness from today's date so all hourly runs agree on the plan ──
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
HOUR  = datetime.now(timezone.utc).hour
seed  = int(hashlib.md5(TODAY.encode()).hexdigest(), 16) % (2**32)
rng   = random.Random(seed)

SCHEDULE_PATH = Path("logs/schedule.json")
SCHEDULE_PATH.parent.mkdir(exist_ok=True)

# ── Load or generate today's schedule ────────────────────────────────────────
if SCHEDULE_PATH.exists():
    schedule = json.loads(SCHEDULE_PATH.read_text())
    if schedule.get("date") != TODAY:
        schedule = None  # stale, regenerate
else:
    schedule = None

if schedule is None:
    # ~25% chance of being a total skip day
    is_skip_day = rng.random() < 0.25

    if is_skip_day:
        commit_hours = []
    else:
        # Number of commits: weighted toward 1-4, occasionally up to 10
        weights = [0, 20, 18, 15, 12, 10, 8, 6, 5, 3, 3]  # index = count
        num_commits = rng.choices(range(11), weights=weights)[0]
        num_commits = max(1, num_commits)  # at least 1 on active days

        # Pick realistic hours (weighted: more activity 8am-10pm UTC = 3am-5pm NYC)
        hour_pool = [9, 14, 19]   # was list(range(8, 23))
        commit_hours = sorted(rng.sample(hour_pool, min(num_commits, len(hour_pool))))

    schedule = {"date": TODAY, "skip": is_skip_day, "commit_hours": commit_hours}
    SCHEDULE_PATH.write_text(json.dumps(schedule, indent=2))
    print(f"📅  New schedule for {TODAY}: skip={is_skip_day}, hours={commit_hours}")

# ── Check if THIS hour should commit ─────────────────────────────────────────
if schedule["skip"] or HOUR not in schedule["commit_hours"]:
    print(f"⏭  Hour {HOUR:02d} — not a commit hour. Skipping.")
    sys.exit(0)

print(f"✅  Hour {HOUR:02d} — committing! Fetching data...")

# ── Commit message pool — realistic and varied ────────────────────────────────
commit_messages = [
    f"data: daily snapshot {TODAY}",
    f"update: refresh market data and trends {TODAY}",
    f"chore: automated data sync {TODAY}",
    f"data: crypto + github trends updated",
    f"update: NASA APOD + quote of the day",
    f"chore: daily data pipeline run",
    f"data: market snapshot and fun facts",
    f"update: morning data refresh {TODAY}",
    f"chore: scheduled content update",
    f"data: trending repos and price sync",
    f"update: daily digest {TODAY}",
    f"chore: routine data fetch",
    f"data: fresh snapshot — crypto, space, code",
]

# Use a different message each hour using seeded randomness
hour_rng = random.Random(seed + HOUR)
msg = hour_rng.choice(commit_messages)

# Write commit message for the workflow to use
with open("/tmp/commit_msg.txt", "w") as f:
    f.write(msg)
print(f"💬  Commit message: {msg}")

# ── Now actually run the data fetcher ─────────────────────────────────────────
import importlib.util, subprocess, sys
result = subprocess.run([sys.executable, "scripts/fetch_daily.py"], capture_output=False)
sys.exit(result.returncode)
