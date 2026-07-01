# CLI Reference

Run `python -m karuma --help` or `python -m karuma <command> --help` for built-in help.

## Global options

```
usage: karuma [-h] [--version] [-c CONFIG] [-t TOKENS] [-p PROXIES] [-m MEMBERS]
              [--log-level {DEBUG,INFO,WARNING,ERROR}] [--log-file LOG_FILE]
              [--no-color] [--skip-disclaimer] [--skip-boot]
              [--connect-timeout CONNECT_TIMEOUT]
              command ...
```

| Option | Description |
|--------|-------------|
| `-c`, `--config` | Path to config.json (default: `config.json`) |
| `-t`, `--tokens` | Tokens file (default: `tokens.txt`) |
| `-p`, `--proxies` | Proxies file (default: `proxies.txt`) |
| `-m`, `--members` | Member IDs file (default: `members.txt`) |
| `--log-level` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `--log-file` | Log file path; `none` disables file logging |
| `--no-color` | Plain console output |
| `--skip-disclaimer` | Skip TOS banner |
| `--skip-boot` | Skip boot animation |
| `--connect-timeout` | Login wait timeout in seconds (default: 60) |
| `--version` | Print version and exit |

If no subcommand is given, the interactive **menu** starts.

## Commands

### menu

Interactive numbered menu (default behavior).

```bash
python -m karuma
python -m karuma menu
python -m karuma --skip-boot --log-level DEBUG menu
```

### list-servers

List guilds on the primary account with permissions and permanent invites.

```bash
python -m karuma list-servers
```

Exits after listing. Closes all client connections.

### leave-all

Leave every server on the primary account. Prompts for confirmation.

```bash
python -m karuma leave-all
```

### scrape

Fast member scrape via invite link. Joins the server if needed, calls `fetch_members()`, appends IDs to `members.txt`.

```bash
python -m karuma scrape --invite https://discord.gg/example
python -m karuma scrape --invite discord.gg/example
```

| Argument | Required | Description |
|----------|----------|-------------|
| `--invite` | yes | Discord invite URL or code |

### deep-scrape

Scrape active users by reading message history across accessible text channels. Slower but works when member lists are hidden.

```bash
python -m karuma deep-scrape --invite https://discord.gg/example
```

Prompts for messages-per-channel limit when run from the interactive menu. From CLI, uses default 1000 when invoked via menu path only — CLI always passes invite; limit is prompted at runtime in menu mode.

### mass-dm-file

Send DMs to user IDs listed in `members.txt`.

```bash
python -m karuma mass-dm-file
python -m karuma mass-dm-file --limit 50
```

| Argument | Required | Description |
|----------|----------|-------------|
| `--limit` | no | Max users to DM, taken from the bottom of the file |

Prompts for message type and content interactively.

### mass-dm-server

Mass DM all members in a guild. Uses `fetch_members()` for a complete list.

```bash
python -m karuma mass-dm-server --guild-id 123456789012345678
```

| Argument | Required | Description |
|----------|----------|-------------|
| `--guild-id` | yes | Target guild snowflake ID |

Distributes sends across all connected accounts.

### mass-dm-all

Mass DM every non-bot user visible in the client user cache across all accounts.

```bash
python -m karuma mass-dm-all
```

### nuke

Destructive server cleanup: ban members, delete channels, roles, emojis, and stickers. Requires permissions; skips steps where permissions are missing.

```bash
python -m karuma nuke --guild-id 123456789012345678
```

Uses the **primary** account only. Prompts for ban reason and permission confirmations.

### raid

Server raid actions: rename, create channels/roles, change nicknames. Uses primary account.

```bash
python -m karuma raid --guild-id 123456789012345678
```

Prompts for raid parameters interactively.

## Examples

```bash
# Verbose debug session
python -m karuma --log-level DEBUG --skip-disclaimer menu

# Custom config and tokens location
python -m karuma -c prod.json -t accounts.txt list-servers

# Scrape then mass DM (two steps)
python -m karuma scrape --invite https://discord.gg/example
python -m karuma mass-dm-file --limit 100

# No log file, plain output
python -m karuma --log-file none --no-color list-servers
```

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Runtime error (bad tokens, missing config, etc.) |
| `130` | Interrupted (Ctrl+C) |

## Makefile shortcuts

```bash
make run            # python -m karuma menu
make list-servers   # python -m karuma list-servers
make check          # compileall
make clean          # remove caches and karuma.log
```
