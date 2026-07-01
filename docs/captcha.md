# Captcha Setup

Discord may require hCaptcha when sending DMs or joining servers. Karuma handles this through `handle_captcha` on the Discord client. Set `captcha_service` in `config.json`.

## Services

| Service | Config value | Requires API key | Requires proxy |
|---------|--------------|------------------|----------------|
| Manual (browser) | `manual` | no | no |
| 2Captcha | `2captcha` | yes | strongly recommended |
| Nopecha | `nopecha` | yes | strongly recommended |

## Manual (default)

Best for single-account use without paid captcha services.

1. Set in `config.json`:
   ```json
   {
     "captcha_service": "manual"
   }
   ```
2. Start Karuma. A local server binds to `127.0.0.1:5050–5099`.
3. Open https://discord.com/channels/@me in your browser (Karuma opens it automatically).
4. Open DevTools → Console (F12).
5. Paste the JavaScript snippet printed to the console/log on startup.
6. When a captcha is triggered, an overlay appears in Discord — solve it there.

The script polls the local server and submits the token back to Karuma.

Timeout: **5 minutes** per captcha challenge.

### Multi-account

Each account gets its own pending captcha slot keyed by username, so concurrent captchas from multiple tokens do not overwrite each other.

## 2Captcha

1. Get an API key from [2captcha.com](https://2captcha.com).
2. Configure:
   ```json
   {
     "captcha_service": "2captcha",
     "captcha_api_key": "YOUR_REAL_API_KEY"
   }
   ```
3. Add matching proxies to `proxies.txt` (one per token).

Karuma sends sitekey, page URL, user-agent, rqdata (enterprise), and proxy details to 2Captcha. Polls for up to **300 seconds**.

### Proxy format for 2Captcha

The client's proxy is parsed and forwarded automatically:

```
http://user:pass@host:port
socks5://user:pass@host:port
```

Without a proxy, solutions may be rejected by Discord due to IP mismatch — you'll see repeated captcha loops.

## Nopecha

1. Get an API key from [nopecha.com](https://nopecha.com).
2. Configure:
   ```json
   {
     "captcha_service": "nopecha",
     "captcha_api_key": "YOUR_REAL_API_KEY"
   }
   ```
3. Add proxies to `proxies.txt`.

Polls the Nopecha token API for up to **120 seconds**.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Infinite captcha loop | 2Captcha/Nopecha IP ≠ account IP | Add residential proxies in `proxies.txt` |
| `No captcha_api_key set` | Missing or placeholder key | Set a real key or switch to `manual` |
| Manual solve times out | Browser script not running | Re-paste the JS snippet in DevTools |
| `Failed to apply X-Super-Properties` | Invalid base64 in config | Clear `x_super_properties` or paste a fresh value |
| Placeholder key warning on startup | Default config value detected | Replace key or use `manual` service |

## Debug logging

```bash
python -m karuma --log-level DEBUG menu
```

Check `karuma.log` for captcha task IDs, proxy forwarding, and solver errors.
