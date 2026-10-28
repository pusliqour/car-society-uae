# Car Society UAE

Public CSAE website and continuously updated UAE car-event calendar.

- **Live site:** https://pusliqour.github.io/car-society-uae/
- **Calendar data:** `data/events.json`
- **Publishing:** GitHub Pages from `main` `/`
- **Updates:** an allowlisted Telegram bot previews submissions and commits approved events through the GitHub Contents API

## How calendar updates work

1. Send the private Telegram bot an Instagram URL plus labeled event details.
2. The bot validates the source, date, time, event type, and required fields.
3. The bot replies with a concise calendar preview.
4. An allowed chat presses **Approve & publish**.
5. The bot reads the current `data/events.json` and its GitHub SHA.
6. It rejects duplicate event IDs or Instagram sources.
7. It commits the sorted JSON update to `main` through GitHub.
8. GitHub Pages rebuilds the live calendar automatically.

Receiving a link never writes to GitHub. Approval is one-time, expires after 24 hours, and is bound to the Telegram chat that submitted it.

## Telegram submission format

```text
https://www.instagram.com/p/ABC123/
Club: Dubai Night Riders
Event: Mountain Drive
Date: 2026-11-14
Time: 20:00
Type: Drive
Emirate: Dubai
Location: Last Exit
Details: Meet at 19:30. Depart at 20:00. Bring a full tank.
```

Accepted types: `Meet`, `Drive`, `Track day`, `Show`, `Off-road`, `Motorsport`, `Other`.

Times are interpreted as UAE/GST calendar display values. The original Instagram URL is preserved as the event source.

## Local website preview

The browser must load `data/events.json`, so use an HTTP server instead of opening the file directly:

```bash
python3 -m http.server 8080
```

Then open http://127.0.0.1:8080/.

## Bot setup

Requirements: Python 3.9+ and an authenticated `gh` CLI, or a GitHub token with repository Contents write access.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
mkdir -p .secrets
cp .env.example .secrets/csae.env
chmod 600 .secrets/csae.env
```

Edit `.secrets/csae.env` and set:

- `TELEGRAM_BOT_TOKEN`: BotFather token.
- `TELEGRAM_ALLOWED_CHAT_IDS`: one or more numeric chat IDs separated by commas.
- `GITHUB_TOKEN`: optional on this Mac; `scripts/run_bot.sh` falls back to `gh auth token` without printing it.

Never run the bot with an empty chat allowlist.

Start it with:

```bash
./scripts/run_bot.sh
```

## Validation and tests

```bash
PYTHONPATH=src python3 -m csae.validate
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

`csae.validate` checks IDs, required fields, ISO dates/times, HTTPS source links, and multi-day ordering before bot commits are made.

## Design colors

The website retains the supplied CSAE palette:

- Asphalt: `#080a11`
- Amber: `#ff9a1f`
- Heat pink: `#ff2d6f`
- HUD cyan: `#5fe3ff`
- Confirmed green: `#62f5a6`
