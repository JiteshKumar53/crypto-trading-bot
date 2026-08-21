# Stocks News → Telegram

Pulls stock-market headlines from RSS feeds, filters them against a watchlist,
and delivers them to Telegram as scheduled digests plus breaking-news alerts.

No API keys are needed for the news itself — the default feeds are public RSS.
The only credentials required are for your own Telegram bot.

## Setup

### 1. Create a bot and get the credentials

1. Message [@BotFather](https://t.me/BotFather) on Telegram, send `/newbot`,
   and follow the prompts. It replies with a token like `123456:ABC-DEF...`.
2. Get your chat id. With the token set, send any message to your bot (or add
   it to the group/channel and post there), then run:

   ```bash
   cd crypto-trading-bot/bots/news_system
   python3 news_daemon.py --mode chatid
   ```

   It prints a ready-to-paste line per chat it can see:

   ```
   TELEGRAM_CHAT_ID=123456789    # private: Alex @yourhandle
   TELEGRAM_CHAT_ID=-1001234567890   # supergroup: Trading Desk
   ```

   This reads pending updates only — it sends nothing. It returns no chats if
   the bot has never been messaged, or if a webhook is configured.

### 2. Add them to the environment

Append to `crypto-trading-bot/.env` (already git-ignored — never commit these):

```
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=-1001234567890
```

The daemon reads that file automatically, and real environment variables win
over it.

### 3. Verify delivery

```bash
cd crypto-trading-bot/bots/news_system
python3 news_daemon.py --mode test
```

A confirmation message with your watchlist and schedule should arrive in the
chat. If it does not, the log names the reason.

## Running

```bash
# List chats the bot can post to
python3 news_daemon.py --mode chatid

# One grouped digest of everything new
python3 news_daemon.py --mode digest

# Breaking headlines only (score >= filters.alert_threshold)
python3 news_daemon.py --mode alerts

# Render to stdout without sending, and without marking anything as seen
python3 news_daemon.py --mode digest --dry-run

# Scheduled operation: digests at the configured times, alerts on an interval
python3 news_loop.py
# or, detached, with logging:
../../../scripts/run_news_loop.sh
```

Exit codes: `0` success (including "nothing new"), `1` delivery failure,
`2` config error, `3` Telegram rejected the request, `4` network unreachable.

## Configuration

Everything is in [`config/news.yaml`](../../config/news.yaml).

| Section | What it controls |
| --- | --- |
| `watchlist` | Tickers tracked, plus the company names/aliases matched in headlines |
| `feeds.per_ticker` | Feeds fetched once per symbol; `{symbol}` is substituted |
| `feeds.market` | Market-wide feeds, fetched once per cycle |
| `filters.keywords` | Scoring tiers — `high` +3, `medium` +2, `low` +1 |
| `filters.alert_threshold` | Score at which a headline interrupts instead of waiting for the digest |
| `filters.blocklist` | Phrases that drop a headline outright |
| `schedule.digest_times` | Local times digests are sent |
| `schedule.alert_poll_minutes` | How often the loop polls for breaking news |
| `telegram.quiet_hours` | Window where messages arrive without a notification sound |
| `telegram.quiet_hours_timezone` | Whose clock quiet hours follow — see below |

### How a headline is scored

```
score = keyword hits (high 3 / medium 2 / low 1)
      + 2 if it arrived on a per-ticker feed
      + 2 if under 2h old, or +1 if under 6h
```

Ranking uses the total. The **relevance gate** deliberately uses keyword hits
only: a headline that names no watchlist company is kept only if it carries a
real keyword, so the freshness bonus cannot smuggle in off-topic news.

### Matching is case-sensitive

Both tickers and company names are matched case-sensitively, so `meta
description tips` is not reported as META news and `i spy a bargain` is not
reported as SPY news. Headlines capitalize company names, so the trade-off
costs almost nothing.

### Quiet hours follow *your* clock, not the market's

`schedule.timezone` is the market's (`America/New_York`), because digest times
track the trading day. Quiet hours are different: they should follow wherever
you are, so `telegram.quiet_hours_timezone` is set separately.

Leaving them coupled is a subtle trap. At GMT+2, 09:00 local is 03:00 in New
York — inside a `[22, 7]` window — so every alert through your entire morning
would arrive with no notification sound. It ships as `Europe/Berlin` (GMT+2);
change it to your actual zone.

## Behaviour worth knowing

- **Nothing is sent twice.** Delivered headlines are recorded in
  `logs/news_seen.json` and suppressed for `state.retention_days`. The same
  story arriving from two feeds collapses to one entry, because URLs are
  normalized (scheme, `www.`, and `utm_*`/`fbclid`/`gclid` params are stripped)
  before hashing.
- **Alerts and digests compose.** A headline pushed as an alert is already
  marked seen, so the next digest carries only what has not been sent.
- **Delivery failure is not silent.** If Telegram rejects a digest, the items
  are *not* marked as seen, so the next run retries them.
- **A dead feed cannot stop a run.** Fetch failures are logged with their
  reason and skipped. Feeds are fetched concurrently.
- **Restarts do not re-send.** `news_loop.py` treats digest slots that already
  passed today as fired. Anything missed while it was down still shows up in
  the next digest, since only *delivered* headlines are suppressed.

## Tests

```bash
cd crypto-trading-bot
python3 -m pytest bots/news_system/test_news_system.py -v
```

85 tests, no network access required.

## Files

| File | Purpose |
| --- | --- |
| `news_daemon.py` | CLI entry point — `digest`, `alerts`, `test`, `chatid` modes |
| `news_loop.py` | Long-lived scheduler that shells out to the daemon |
| `config.py` | Loads `news.yaml`, applies defaults, reads credentials |
| `sources.py` | Concurrent RSS/Atom fetching and parsing (stdlib XML) |
| `filters.py` | Symbol matching, scoring, de-duplication, ranking |
| `formatter.py` | Telegram HTML rendering for digests and alerts |
| `telegram_client.py` | Bot API sender with retry, rate-limit and 4096-char handling |
| `state.py` | Atomic seen-item ledger |

## Adding a feed

Any RSS 2.0 or Atom URL works. Add it under `feeds.market` (or
`feeds.per_ticker` with `{symbol}` in the URL) and check it parses:

```bash
python3 news_daemon.py --mode digest --dry-run
```

The log prints `FEED OK <name> — N items` or `FEED FAIL <name> — <reason>` for
each one.
