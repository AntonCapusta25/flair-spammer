# Configuration

Karuma reads settings from `config.json` and several optional files in the project root. CLI flags override config file values where noted.

## config.json

Example template: [examples/config.json.example](../examples/config.json.example)

```json
{
  "token": "",
  "skip_disclaimer": false,
  "skip_booting": false,
  "minimum_dm_delay": 1.0,
  "maximum_dm_delay": 3.0,
  "minimum_ban_delay": 1.0,
  "maximum_ban_delay": 3.0,
  "minimum_general_delay": 0.5,
  "maximum_general_delay": 1.5,
  "captcha_api_key": "",
  "captcha_service": "manual",
  "x_super_properties": ""
}
```

### Fields

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `token` | string | `""` | Fallback account token if `tokens.txt` is missing |
| `skip_disclaimer` | bool | `false` | Skip the TOS disclaimer on startup |
| `skip_booting` | bool | `false` | Skip the boot animation |
| `minimum_dm_delay` | float | `1.0` | Minimum seconds between mass DMs |
| `maximum_dm_delay` | float | `3.0` | Maximum seconds between mass DMs |
| `minimum_ban_delay` | float | `1.0` | Minimum seconds between ban actions |
| `maximum_ban_delay` | float | `3.0` | Maximum seconds between ban actions |
| `minimum_general_delay` | float | `0.5` | Minimum delay for channels, roles, etc. |
| `maximum_general_delay` | float | `1.5` | Maximum delay for channels, roles, etc. |
| `captcha_api_key` | string | `""` | API key for 2Captcha or Nopecha |
| `captcha_service` | string | `manual` | `manual`, `2captcha`, or `nopecha` |
| `x_super_properties` | string | `""` | Base64-encoded Discord client fingerprint (optional) |

Delays use a random value between min and max for each action to reduce rate-limit triggers.

### Placeholder detection

If `captcha_api_key` is empty or a placeholder (`"Your Captcha API Key Here"`), Karuma automatically falls back to **manual** captcha solving regardless of `captcha_service`.

### X-Super-Properties

Optional. Must be valid base64-encoded JSON copied from a real Discord browser session. If invalid or corrupted, Karuma logs an error and continues with default client headers.

Leave empty (`""`) to use discord.py-self defaults.

## tokens.txt

Preferred way to supply account tokens.

```
# One token per line. Lines starting with # are ignored.
YOUR_TOKEN_1
YOUR_TOKEN_2
```

CLI override: `-t /path/to/tokens.txt`

If `tokens.txt` is missing, Karuma falls back to `"token"` in `config.json` (unless it is the placeholder `"Your Token Here"`).

## proxies.txt

Optional. One proxy per line, assigned round-robin to tokens.

```
# Supported formats (http prefix added automatically if omitted):
user:pass@1.2.3.4:8080
http://user:pass@1.2.3.4:8080
socks5://user:pass@1.2.3.4:1080
```

CLI override: `-p /path/to/proxies.txt`

**Strongly recommended** when using 2Captcha or Nopecha — Discord hCaptcha Enterprise often requires the solver IP to match the account IP.

## members.txt

Output from scrape commands and input for mass DM from file. One numeric user ID per line.

CLI override: `-m /path/to/members.txt`

## CLI-only settings

These are not stored in `config.json`:

| Flag | Default | Description |
|------|---------|-------------|
| `--connect-timeout` | `60` | Seconds to wait for accounts to connect |
| `--log-level` | `INFO` | Console log verbosity |
| `--log-file` | `karuma.log` | Log file path; use `none` to disable |
| `--no-color` | off | Disable colored console logs |

## Path overrides

All file paths can be changed from the CLI without editing defaults:

```bash
python -m karuma -c my-config.json -t alt-tokens.txt -p alt-proxies.txt -m ids.txt menu
```
