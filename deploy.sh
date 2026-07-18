#!/bin/bash
# Deploy dashboard to GitHub Pages
set -e
cd /home/hermes/northern-mile-dashboard

echo "=== Deploy $(date) ==="

# 1. Collect fresh data
echo "[1/4] Collecting data..."
python3 scripts/collector.py 2>&1
COLLECT_EXIT=$?

# 2. Health check — record status for each source
echo "[2/4] Health check..."
python3 -c "
import json, os, sys
sys.path.insert(0, 'scripts')
from health_tracker import record_success, record_failure

data_dir = 'data'
sources = {
    'fuel': 'fuel.json',
    'exchange': 'exchange.json', 
    'border': 'border.json',
    'incidents': 'incidents.json',
    'market': 'market.json',
    'news': 'news.json',
    'theft': 'theft.json'
}

for src, filename in sources.items():
    path = os.path.join(data_dir, filename)
    try:
        if os.path.exists(path):
            with open(path) as f:
                d = json.load(f)
            # Check if data has content (not empty)
            if d and (d.get('updated') or d.get('current') or len(d.get('incidents', [])) > 0 or 
                      len(d.get('headlines', [])) > 0 or d.get('diesel_national_avg')):
                record_success(src)
            else:
                record_failure(src, 'Empty data')
        else:
            record_failure(src, 'File missing')
    except Exception as e:
        record_failure(src, str(e))
print('Health recorded.')
" 2>&1

# 3. Copy data to docs and v2
echo "[3/4] Copying data..."
cp data/*.json docs/data/
mkdir -p docs/v2/data && cp data/*.json docs/v2/data/

# 4. Rebuild both
echo "[4/4] Building..."
python3 scripts/build_dashboard.py production
python3 scripts/build_dashboard.py staging

# 5. Commit and push
echo "=== Git push ==="
git add -A
git commit -m "Auto-update $(date '+%Y-%m-%d %H:%M')" || echo "  (nothing to commit)"
git push origin master || echo "  Push failed — check GitHub auth"
echo "Done."
