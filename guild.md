# SAP SuccessFactors Troubleshooting Engine — Developer Guide

## What the Engine Does

The engine takes a user's issue description (and optionally a screenshot), finds the right solution using AI, and outputs a JSON file. That's it. **Your job starts after the JSON is written.**

```
User Input → Engine → JSON file in /results/ → Your Code
```

---

## The JSON Output

Every run produces a file like `results/troubleshoot_vision_20260219_161534.json`. Here's what's inside:

```json
{
  "mode": "vision_enhanced",
  "task_used": {
    "task_number": "1",
    "title": "Admin is unable to access Proxy management",
    "vision_confidence": 1.0
  },
  "playwright_actions": [
    {
      "order": 1,
      "action_type": "fill",
      "visual_target": "Type 'Manage Role Permissions' in search bar"
    },
    {
      "order": 2,
      "action_type": "click",
      "visual_target": "Click on 'Manage Role Permissions' result"
    }
  ]
}
```

The key fields are `playwright_actions` (the steps to perform) and `vision_confidence` (how sure the engine is).

---

## Calling the Engine Directly

```python
from main import Config, TroubleshootingEngine
from PIL import Image

config = Config()
engine = TroubleshootingEngine(config)
engine.initialize()

# Text only
result = engine.troubleshoot_text("Admin cannot access Proxy Management")

# With screenshot
screenshot = Image.open("my_screenshot.png")
result = engine.troubleshoot_with_screenshot("proxy access issue", screenshot)
```

---

## For Playwright Developers

### 1. Watch for new results

```python
from pathlib import Path
import json, time

results_dir = Path("results")
seen = set()

while True:
    for file in results_dir.glob("troubleshoot_vision_*.json"):
        if file.name not in seen:
            seen.add(file.name)
            data = json.loads(file.read_text())
            actions = data.get("playwright_actions", [])
            # pass actions to your executor
    time.sleep(5)
```

### 2. Map action types to Playwright

Each action has an `action_type` and a `visual_target`. Build a simple dispatcher:

| action_type | Playwright approach |
|-------------|---------------------|
| `fill` | Extract quoted text, use `page.get_by_placeholder().fill()` |
| `click` | Extract quoted text, try `get_by_text()` then `get_by_role()` |
| `verify` | Use `expect(element).to_be_visible()` |
| `save` | Find a button with text "Save" |

### 3. Extract the target text

The `visual_target` field uses quoted phrases: `"Type 'Manage Role Permissions' in search bar"`. Pull out what's between the single quotes and use that as your selector value.

```python
import re

def extract_quoted(text):
    match = re.search(r"'([^']+)'", text)
    return match.group(1) if match else text
```

### 4. Decide on confidence thresholds

```
vision_confidence == 1.0   → Automate fully
vision_confidence >= 0.8   → Automate, but review screenshots after
vision_confidence < 0.8    → Show to a human instead
```

### 5. Your overall flow

```
1. Watch /results for new files
2. Load playwright_actions
3. Launch browser
4. Log in (credentials from env vars)
5. Loop through actions, executing each
6. Screenshot after each step
7. Close browser
```

The engine does not handle login — that's yours to build.

---

## For Flask Developers

### 1. Wrap the engine in endpoints

You need at minimum three routes:

```
GET  /health                  → engine status check
POST /troubleshoot/text       → accepts {"issue": "..."}, returns JSON
POST /troubleshoot/screenshot → accepts issue + image, returns JSON
```

### 2. Accept screenshots two ways

**Option A — Base64 JSON:**
```json
{
  "issue": "proxy access issue",
  "screenshot": "<base64 string>"
}
```

**Option B — Multipart form upload:**
```
issue=proxy access issue
screenshot=<file>
```

Pick one (or support both). Decode/open the image into a PIL `Image` object before passing it to the engine.

### 3. Initialize the engine once

```python
engine = TroubleshootingEngine(config)
engine.initialize()  # Do this at startup, not per request
```

### 4. Return consistent error responses

```json
{
  "success": false,
  "error": "Screenshot could not be decoded",
  "error_code": "INVALID_IMAGE"
}
```

Common error cases: missing fields (400), invalid image (400), engine not ready (503), unexpected crash (500).

### 5. Production checklist

- Run with Gunicorn, not Flask's dev server
- Set `MAX_CONTENT_LENGTH` to cap image upload size
- Add rate limiting (screenshots are expensive — limit to ~10/min)
- Store your `GEMINI_API_KEY` in environment variables, not code

---

## Environment Variables

```bash
# Required
GEMINI_API_KEY=your_key_here

# For Playwright automation
SAP_USERNAME=your_username
SAP_PASSWORD=your_password
SAP_INSTANCE_URL=https://your-instance.com
```

---

## Quick Debugging Tips

- Check `/results` first — if the file is there, the engine worked
- Low confidence score? The screenshot may not match any known task
- No actions in the JSON? The engine fell back to text-only mode
- Run `python src/main.py` and use option 3 (test suite) or option 4 (task list) to verify the engine is healthy