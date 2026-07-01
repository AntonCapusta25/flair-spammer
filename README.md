# Karuma — how to start

Tool that logs into Discord with **your account** and lets you scrape members, send mass DMs, etc.

---

## Step 1 — Install

Open terminal in this folder:

```bash
pip install -r requirements.txt
```

---

## Step 2 — Add your token

Create a file named **`tokens.txt`** in this folder.

Put your Discord token inside (one line, nothing else):

```
paste_your_token_here
```

**Do not put the token in config.json.** Only `tokens.txt`.

Multiple accounts? One token per line.

---

## Step 3 — Run

```bash
python -m karuma
```

Pick a number from the menu.

---

## What each file is

| File | What it is | Need it? |
|------|------------|----------|
| `tokens.txt` | Your Discord login token | **Yes** |
| `config.json` | Delays, captcha settings | Already there, optional to edit |
| `proxies.txt` | Proxies (one per line) | No — only if you use paid captcha |
| `members.txt` | List of user IDs to DM | No — created when you scrape |

---

## Menu (what the numbers do)

| # | What happens |
|---|----------------|
| 1 | Destroy a server (ban, delete channels…) |
| 2 | Spam a server (channels, roles, nicknames) |
| 3 | DM everyone in one server |
| 4 | DM all users your account can see |
| 5 | DM users from `members.txt` |
| 6 | Save server member IDs to `members.txt` (fast) |
| 7 | Save active user IDs from chat history (slow) |
| 8 | Show your servers |
| 9 | Leave all servers |
| 10 | Quit |

---

## config.json — only change if you need to

Most people leave it alone. Important fields:

```json
{
  "minimum_dm_delay": 50,
  "maximum_dm_delay": 70,
  "captcha_service": "manual"
}
```

- **Delays** — seconds to wait between messages/actions (higher = safer, slower).
- **captcha_service** — `"manual"` = solve captcha in browser. Use `"2captcha"` only if you pay for 2Captcha.

Ignore `x_super_properties` — leave it empty or delete the line.

---

## Problems?

| Error | Fix |
|-------|-----|
| No tokens found | Create `tokens.txt` with your token |
| Invalid token | Token is wrong or expired — get a new one |
| Captcha loop | Set `"captcha_service": "manual"` in config.json |

More detail: [docs/](docs/) folder (optional).

**Warning:** This breaks Discord rules. Your account can get banned.
