"""
News System — Test Suite
Run: python3 -m pytest bots/news_system/test_news_system.py -v
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import filters
import formatter
import sources
import state
import news_daemon
import telegram_client
from sources import NewsItem

NOW = datetime(2026, 8, 21, 16, 0, tzinfo=timezone.utc)


def make_item(title, hours_ago=1, symbol=None, link=None, summary="", source="Feed"):
    return NewsItem(
        title=title,
        link=link or f"https://example.com/{abs(hash(title)) % 10**8}",
        source=source,
        published=NOW - timedelta(hours=hours_ago),
        summary=summary,
        symbol=symbol,
    )


@pytest.fixture
def cfg():
    return config.load_config()


# ─── sources: parsing ────────────────────────────────────────────────────────

RSS_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Feed</title>
<item>
  <title>Apple &amp; Nvidia beat estimates</title>
  <link>https://example.com/story-one</link>
  <pubDate>Tue, 19 Aug 2026 14:30:00 GMT</pubDate>
  <description>&lt;p&gt;Strong   quarter&lt;/p&gt;</description>
</item>
<item>
  <title>Second story</title>
  <link>https://example.com/story-two</link>
  <pubDate>Tue, 19 Aug 2026 15:00:00 GMT</pubDate>
</item>
</channel></rss>"""

ATOM_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>Atom Feed</title>
<entry>
  <title>Tesla trading halted</title>
  <link rel="alternate" href="https://example.com/atom-one"/>
  <updated>2026-08-19T10:00:00Z</updated>
  <summary>Halt pending news.</summary>
</entry>
</feed>"""


def test_parse_rss_extracts_items():
    items = sources.parse_feed(RSS_SAMPLE, "Feed")
    assert len(items) == 2
    assert items[0].title == "Apple & Nvidia beat estimates"
    assert items[0].link == "https://example.com/story-one"
    assert items[0].summary == "Strong quarter"
    assert items[0].published == datetime(2026, 8, 19, 14, 30, tzinfo=timezone.utc)


def test_parse_atom_extracts_href_link():
    items = sources.parse_feed(ATOM_SAMPLE, "Atom Feed")
    assert len(items) == 1
    assert items[0].link == "https://example.com/atom-one"
    assert items[0].published == datetime(2026, 8, 19, 10, 0, tzinfo=timezone.utc)


def test_parse_feed_carries_symbol_through():
    items = sources.parse_feed(RSS_SAMPLE, "Feed", symbol="AAPL")
    assert all(item.symbol == "AAPL" for item in items)


def test_parse_malformed_xml_returns_empty():
    assert sources.parse_feed("<rss><not closed", "Feed") == []
    assert sources.parse_feed("", "Feed") == []
    assert sources.parse_feed("   ", "Feed") == []


def test_parse_skips_items_without_title_or_link():
    xml = """<rss version="2.0"><channel>
    <item><title>No link here</title></item>
    <item><link>https://example.com/no-title</link></item>
    </channel></rss>"""
    assert sources.parse_feed(xml, "Feed") == []


def test_clean_text_strips_tags_and_entities():
    assert sources.clean_text("<b>Up</b> &amp; &lt;down&gt;") == "Up & <down>"
    assert sources.clean_text("&#39;quoted&#39;") == "'quoted'"
    assert sources.clean_text("a\n\n  b") == "a b"
    assert sources.clean_text("") == ""


def test_parse_date_handles_both_formats_and_garbage():
    assert sources.parse_date("Tue, 19 Aug 2026 14:30:00 GMT").hour == 14
    assert sources.parse_date("2026-08-19T10:00:00Z").hour == 10
    assert sources.parse_date("not a date") is None
    assert sources.parse_date("") is None


def test_parse_date_assumes_utc_when_naive():
    parsed = sources.parse_date("2026-08-19T10:00:00")
    assert parsed.tzinfo is not None
    assert parsed.utcoffset().total_seconds() == 0


# ─── sources: identity / de-duplication ──────────────────────────────────────

def test_uid_ignores_tracking_params_and_scheme():
    a = make_item("Story", link="https://www.example.com/a?utm_source=rss&id=5")
    b = make_item("Story", link="http://example.com/a?id=5")
    assert a.uid == b.uid


def test_uid_distinguishes_different_stories():
    assert make_item("A", link="https://x.com/a").uid != make_item("B", link="https://x.com/b").uid


def test_uid_falls_back_to_title_when_link_missing():
    item = NewsItem(title="Headline", link="", source="Feed")
    assert item.uid == NewsItem(title="Headline", link="", source="Other").uid


def test_age_hours():
    assert make_item("x", hours_ago=3).age_hours(NOW) == pytest.approx(3.0)
    assert NewsItem(title="x", link="y", source="z").age_hours(NOW) is None


# ─── filters: matching ───────────────────────────────────────────────────────

def test_symbol_matched_case_sensitively(cfg):
    matchers = filters.build_matchers(cfg["watchlist"])
    assert "AAPL" in filters.match_symbols(make_item("AAPL rallies"), matchers)
    assert "AAPL" in filters.match_symbols(make_item("$AAPL rallies"), matchers)
    # A lowercase English word must not be read as a ticker.
    assert filters.match_symbols(make_item("i spy a bargain"), matchers) == []


def test_company_name_matched_but_not_lowercase_homograph(cfg):
    matchers = filters.build_matchers(cfg["watchlist"])
    assert "META" in filters.match_symbols(make_item("Meta buys a startup"), matchers)
    assert filters.match_symbols(make_item("meta description tips"), matchers) == []


def test_alias_matches(cfg):
    matchers = filters.build_matchers(cfg["watchlist"])
    assert "GOOGL" in filters.match_symbols(make_item("Google faces probe"), matchers)


def test_substring_does_not_match(cfg):
    matchers = filters.build_matchers(cfg["watchlist"])
    assert filters.match_symbols(make_item("Pineapple harvest report"), matchers) == []


def test_feed_symbol_included_even_without_text_match(cfg):
    matchers = filters.build_matchers(cfg["watchlist"])
    item = make_item("Quiet session for the sector", symbol="MSFT")
    assert filters.match_symbols(item, matchers) == ["MSFT"]


# ─── filters: scoring ────────────────────────────────────────────────────────

def test_keyword_tiers_are_weighted(cfg):
    keywords = cfg["filters"]["keywords"]
    high = filters.score_item(make_item("Q3 earnings beat"), keywords, NOW)
    low = filters.score_item(make_item("Analyst weighs in"), keywords, NOW)
    assert high > low


def test_per_ticker_feed_earns_a_bonus(cfg):
    keywords = cfg["filters"]["keywords"]
    plain = filters.score_item(make_item("Neutral headline"), keywords, NOW)
    tagged = filters.score_item(make_item("Neutral headline", symbol="AAPL"), keywords, NOW)
    assert tagged - plain == filters.PER_TICKER_FEED_BONUS


def test_fresher_news_outranks_older_at_equal_keywords(cfg):
    keywords = cfg["filters"]["keywords"]
    fresh = filters.score_item(make_item("Earnings out", hours_ago=1), keywords, NOW)
    stale = filters.score_item(make_item("Earnings out", hours_ago=12), keywords, NOW)
    assert fresh > stale


def test_keyword_score_excludes_bonuses(cfg):
    keywords = cfg["filters"]["keywords"]
    item = make_item("Earnings beat", hours_ago=1, symbol="AAPL")
    filters.score_item(item, keywords, NOW)
    assert item.keyword_score == 3
    assert item.score > item.keyword_score


# ─── filters: pipeline ───────────────────────────────────────────────────────

def test_blocklisted_headline_dropped(cfg):
    out = filters.filter_and_score([make_item("Sponsored: Apple earnings deal")], cfg, now=NOW)
    assert out == []


def test_stale_headline_dropped(cfg):
    out = filters.filter_and_score([make_item("Apple earnings", hours_ago=48)], cfg, now=NOW)
    assert out == []


def test_undated_headline_survives(cfg):
    item = NewsItem(title="Apple earnings beat", link="https://x.com/u", source="Feed")
    assert len(filters.filter_and_score([item], cfg, now=NOW)) == 1


def test_offtopic_market_headline_dropped(cfg):
    out = filters.filter_and_score([make_item("Best hiking trails this weekend")], cfg, now=NOW)
    assert out == []


def test_market_headline_with_keyword_kept(cfg):
    out = filters.filter_and_score([make_item("Trading halted across the sector")], cfg, now=NOW)
    assert len(out) == 1
    assert out[0].symbols == []


def test_relevance_gate_can_be_disabled(cfg):
    cfg["filters"]["require_relevance_for_market_feeds"] = False
    out = filters.filter_and_score([make_item("Best hiking trails this weekend")], cfg, now=NOW)
    assert len(out) == 1


def test_duplicates_within_batch_collapse(cfg):
    items = [
        make_item("Apple earnings beat", link="https://a.com/s?utm_source=x", source="Yahoo"),
        make_item("Apple earnings beat", link="https://www.a.com/s", source="CNBC"),
    ]
    assert len(filters.filter_and_score(items, cfg, now=NOW)) == 1


def test_previously_seen_items_excluded(cfg):
    item = make_item("Apple earnings beat")
    assert filters.filter_and_score([item], cfg, seen_uids={item.uid}, now=NOW) == []


def test_results_ranked_best_first(cfg):
    items = [
        make_item("Apple analyst note", hours_ago=5),
        make_item("Apple earnings beat and guidance raised", hours_ago=1),
    ]
    out = filters.filter_and_score(items, cfg, now=NOW)
    assert out[0].title.startswith("Apple earnings")
    assert out[0].score > out[1].score


def test_cap_per_symbol_limits_one_noisy_ticker():
    items = []
    for i in range(5):
        item = make_item(f"Apple story {i}")
        item.symbols = ["AAPL"]
        items.append(item)
    assert len(filters.cap_per_symbol(items, 2)) == 2
    assert len(filters.cap_per_symbol(items, 0)) == 5


def test_cap_per_symbol_keeps_unmatched_items():
    item = make_item("Market wide story")
    item.symbols = []
    assert filters.cap_per_symbol([item], 1) == [item]


def test_select_for_digest_applies_total_cap(cfg):
    cfg["filters"]["max_items_per_digest"] = 2
    cfg["filters"]["max_items_per_symbol"] = 10
    items = filters.filter_and_score(
        [make_item(f"Apple earnings update {i}") for i in range(5)], cfg, now=NOW
    )
    assert len(filters.select_for_digest(items, cfg)) == 2


def test_select_for_alerts_uses_threshold(cfg):
    items = filters.filter_and_score(
        [
            make_item("Apple earnings beat, guidance raised", hours_ago=1),
            make_item("Apple supplier chatter", hours_ago=5),
        ],
        cfg,
        now=NOW,
    )
    urgent = filters.select_for_alerts(items, cfg)
    assert len(urgent) == 1
    assert all(item.score >= cfg["filters"]["alert_threshold"] for item in urgent)


def test_group_by_symbol_puts_unmatched_under_market():
    matched = make_item("Apple news")
    matched.symbols = ["AAPL"]
    unmatched = make_item("Sector news")
    unmatched.symbols = []
    groups = filters.group_by_symbol([matched, unmatched])
    assert groups["AAPL"] == [matched]
    assert groups[formatter.MARKET_GROUP] == [unmatched]


# ─── state ───────────────────────────────────────────────────────────────────

def test_load_seen_missing_file(tmp_path):
    assert state.load_seen(str(tmp_path / "nope.json")) == {}


def test_load_seen_corrupt_file(tmp_path):
    path = tmp_path / "seen.json"
    path.write_text("{not json")
    assert state.load_seen(str(path)) == {}


def test_load_seen_wrong_shape(tmp_path):
    path = tmp_path / "seen.json"
    path.write_text('["a", "b"]')
    assert state.load_seen(str(path)) == {}


def test_save_and_reload_roundtrip(tmp_path):
    path = str(tmp_path / "logs" / "seen.json")
    state.save_seen(path, {"abc": "2026-08-21T10:00:00Z"}, retention_days=7, now=NOW)
    assert state.load_seen(path) == {"abc": "2026-08-21T10:00:00Z"}


def test_save_leaves_no_temp_files(tmp_path):
    path = str(tmp_path / "seen.json")
    state.save_seen(path, {"abc": "2026-08-21T10:00:00Z"}, retention_days=7, now=NOW)
    assert os.listdir(tmp_path) == ["seen.json"]


def test_prune_drops_expired_entries():
    seen = {
        "fresh": "2026-08-20T10:00:00Z",
        "stale": "2026-08-01T10:00:00Z",
        "unparseable": "whenever",
    }
    pruned = state.prune(seen, retention_days=7, now=NOW)
    assert "fresh" in pruned
    assert "stale" not in pruned
    assert "unparseable" in pruned


def test_mark_sent_stamps_uids():
    seen = state.mark_sent({}, ["a", "b"], now=NOW)
    assert seen == {"a": "2026-08-21T16:00:00Z", "b": "2026-08-21T16:00:00Z"}


# ─── telegram client ─────────────────────────────────────────────────────────

def test_escape_handles_html_specials():
    assert telegram_client.escape("Apple & <Nvidia>") == "Apple &amp; &lt;Nvidia&gt;"


def test_split_message_returns_single_chunk_when_short():
    assert telegram_client.split_message("short", 100) == ["short"]


def test_split_message_empty():
    assert telegram_client.split_message("", 100) == []


def test_split_message_breaks_on_blank_lines():
    text = "\n\n".join("x" * 50 for _ in range(6))
    chunks = telegram_client.split_message(text, 120)
    assert len(chunks) > 1
    assert all(len(chunk) <= 120 for chunk in chunks)


def test_split_message_never_splits_a_line_that_fits():
    text = "\n".join(f"<a href='u'>line {i}</a>" for i in range(20))
    chunks = telegram_client.split_message(text, 100)
    for chunk in chunks:
        for line in chunk.split("\n"):
            assert line.count("<a") == line.count("</a>")


def test_split_message_hard_splits_an_oversized_line():
    chunks = telegram_client.split_message("y" * 500, 200)
    assert [len(chunk) for chunk in chunks] == [200, 200, 100]


def test_split_message_respects_api_hard_limit():
    chunks = telegram_client.split_message("z" * 9000, 99999)
    assert all(len(chunk) <= telegram_client.TELEGRAM_MAX_CHARS for chunk in chunks)


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


def test_dry_run_sends_nothing(monkeypatch):
    def explode(*args, **kwargs):
        raise AssertionError("dry run must not hit the network")

    monkeypatch.setattr(telegram_client.requests, "post", explode)
    client = telegram_client.TelegramClient("t", "c", dry_run=True)
    assert client.send("hello") is True


def test_send_success(monkeypatch):
    calls = []

    def fake_post(url, json=None, timeout=None):
        calls.append(json)
        return FakeResponse(200, {"ok": True, "result": {"message_id": 1}})

    monkeypatch.setattr(telegram_client.requests, "post", fake_post)
    client = telegram_client.TelegramClient("t", "chat-1")
    assert client.send("hello", silent=True) is True
    assert calls[0]["chat_id"] == "chat-1"
    assert calls[0]["parse_mode"] == "HTML"
    assert calls[0]["disable_notification"] is True


def test_send_retries_after_rate_limit(monkeypatch):
    responses = [
        FakeResponse(429, {"ok": False, "parameters": {"retry_after": 0}}),
        FakeResponse(200, {"ok": True, "result": {}}),
    ]
    monkeypatch.setattr(telegram_client.time, "sleep", lambda _s: None)
    monkeypatch.setattr(
        telegram_client.requests, "post", lambda *a, **k: responses.pop(0)
    )
    client = telegram_client.TelegramClient("t", "c")
    assert client.send("hello") is True
    assert responses == []


def test_send_raises_on_bad_credentials(monkeypatch):
    monkeypatch.setattr(
        telegram_client.requests,
        "post",
        lambda *a, **k: FakeResponse(401, {"ok": False, "description": "Unauthorized"}),
    )
    client = telegram_client.TelegramClient("bad", "c")
    with pytest.raises(telegram_client.TelegramError):
        client.send("hello")


def test_send_gives_up_after_retries_on_server_error(monkeypatch):
    monkeypatch.setattr(telegram_client.time, "sleep", lambda _s: None)
    monkeypatch.setattr(
        telegram_client.requests,
        "post",
        lambda *a, **k: FakeResponse(500, {"ok": False, "description": "boom"}),
    )
    client = telegram_client.TelegramClient("t", "c", retries=2)
    assert client.send("hello") is False


def test_send_survives_non_json_response(monkeypatch):
    class Garbage:
        status_code = 502
        text = "<html>bad gateway</html>"

        def json(self):
            raise ValueError("not json")

    monkeypatch.setattr(telegram_client.time, "sleep", lambda _s: None)
    monkeypatch.setattr(telegram_client.requests, "post", lambda *a, **k: Garbage())
    client = telegram_client.TelegramClient("t", "c", retries=1)
    assert client.send("hello") is False


# ─── formatter ───────────────────────────────────────────────────────────────

def test_relative_age_scales():
    assert formatter.relative_age(NOW - timedelta(minutes=5), NOW) == "5m ago"
    assert formatter.relative_age(NOW - timedelta(hours=3), NOW) == "3h ago"
    assert formatter.relative_age(NOW - timedelta(days=2), NOW) == "2d ago"
    assert formatter.relative_age(None, NOW) == "undated"


def test_empty_digest_renders_nothing(cfg):
    assert formatter.format_digest([], cfg) == ""


def test_digest_groups_and_escapes(cfg):
    items = filters.filter_and_score(
        [
            make_item("Apple earnings beat & <guidance> raised", hours_ago=1),
            make_item("Trading halted after merger news", hours_ago=1),
        ],
        cfg,
        now=NOW,
    )
    text = formatter.format_digest(items, cfg, label="Test Digest", now=NOW)
    assert "<b>$AAPL</b> · Apple" in text
    assert f"{formatter.MARKET_EMOJI} <b>Market</b>" in text
    assert "&amp; &lt;guidance&gt;" in text
    assert "Test Digest" in text


def test_digest_fits_in_one_telegram_message(cfg):
    items = filters.filter_and_score(
        [make_item(f"Apple earnings update number {i}", hours_ago=1) for i in range(12)],
        cfg,
        now=NOW,
    )
    text = formatter.format_digest(filters.select_for_digest(items, cfg), cfg, now=NOW)
    chunks = telegram_client.split_message(text, cfg["telegram"]["max_message_chars"])
    assert all(len(chunk) <= telegram_client.TELEGRAM_MAX_CHARS for chunk in chunks)


def test_alert_includes_symbol_and_score(cfg):
    item = filters.filter_and_score(
        [make_item("Nvidia downgrade after profit warning", hours_ago=1)], cfg, now=NOW
    )[0]
    text = formatter.format_alert(item, cfg, now=NOW)
    assert formatter.ALERT_EMOJI in text
    assert "$NVDA" in text
    assert f"score {item.score}" in text


def test_alert_for_unmatched_item_says_market(cfg):
    item = filters.filter_and_score(
        [make_item("Trading halted across the sector", hours_ago=1)], cfg, now=NOW
    )[0]
    assert "<b>Market</b>" in formatter.format_alert(item, cfg, now=NOW)


def test_quiet_hours_window_wraps_midnight(cfg):
    cfg["telegram"]["quiet_hours"] = [22, 7]
    assert formatter.is_quiet_hour(cfg, datetime(2026, 8, 21, 23, 0)) is True
    assert formatter.is_quiet_hour(cfg, datetime(2026, 8, 21, 3, 0)) is True
    assert formatter.is_quiet_hour(cfg, datetime(2026, 8, 21, 9, 0)) is False


def test_quiet_hours_same_day_window(cfg):
    cfg["telegram"]["quiet_hours"] = [1, 5]
    assert formatter.is_quiet_hour(cfg, datetime(2026, 8, 21, 3, 0)) is True
    assert formatter.is_quiet_hour(cfg, datetime(2026, 8, 21, 6, 0)) is False


def test_quiet_hours_disabled_when_unset(cfg):
    cfg["telegram"]["quiet_hours"] = []
    assert formatter.is_quiet_hour(cfg, datetime(2026, 8, 21, 23, 0)) is False


# ─── config ──────────────────────────────────────────────────────────────────

def test_shipped_config_loads(cfg):
    assert cfg["watchlist"]
    assert cfg["schedule"]["timezone"]
    assert cfg["telegram"]["max_message_chars"] <= telegram_client.TELEGRAM_MAX_CHARS


def test_missing_config_raises():
    with pytest.raises(config.ConfigError):
        config.load_config("/nonexistent/news.yaml")


def test_empty_watchlist_raises(tmp_path):
    path = tmp_path / "news.yaml"
    path.write_text("watchlist: []\n")
    with pytest.raises(config.ConfigError):
        config.load_config(str(path))


def test_defaults_applied_to_sparse_config(tmp_path):
    path = tmp_path / "news.yaml"
    path.write_text("watchlist:\n  - symbol: AAPL\n    name: Apple\n")
    loaded = config.load_config(str(path))
    assert loaded["schedule"]["timezone"] == "America/New_York"
    assert loaded["filters"]["max_age_hours"] == 24
    assert loaded["network"]["retries"] == 3


def test_per_ticker_feeds_expand_across_watchlist(cfg):
    targets = config.resolve_feed_urls(cfg)
    per_ticker = [t for t in targets if t["symbol"]]
    assert len(per_ticker) == len(cfg["watchlist"])
    assert all("{symbol}" not in t["url"] for t in targets)


def test_disabled_feeds_are_skipped(cfg):
    names = {t["name"] for t in config.resolve_feed_urls(cfg)}
    disabled = [
        f["name"]
        for f in cfg["feeds"]["per_ticker"] + cfg["feeds"]["market"]
        if not f.get("enabled", True)
    ]
    assert all(name not in names for name in disabled)


def test_credentials_error_names_missing_variables(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    with pytest.raises(config.ConfigError) as excinfo:
        config.telegram_credentials()
    assert "TELEGRAM_BOT_TOKEN" in str(excinfo.value)
    assert "TELEGRAM_CHAT_ID" in str(excinfo.value)


def test_credentials_read_from_environment(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "  token  ")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100123")
    assert config.telegram_credentials() == {"token": "token", "chat_id": "-100123"}


# ─── chat discovery ──────────────────────────────────────────────────────────

def test_extract_chats_reads_plain_messages():
    updates = [{"update_id": 1, "message": {"chat": {
        "id": 123456789, "type": "private", "first_name": "Alex", "username": "yourhandle"}}}]
    chats = news_daemon.extract_chats(updates)
    assert chats == [{
        "id": 123456789, "type": "private", "title": "Alex", "username": "yourhandle"}]


def test_extract_chats_reads_groups_and_channels():
    updates = [
        {"channel_post": {"chat": {"id": -100999, "type": "channel", "title": "Alerts"}}},
        {"my_chat_member": {"chat": {"id": -100888, "type": "supergroup", "title": "Desk"}}},
    ]
    ids = {chat["id"] for chat in news_daemon.extract_chats(updates)}
    assert ids == {-100999, -100888}


def test_extract_chats_deduplicates_repeat_messages():
    chat = {"id": 42, "type": "private", "first_name": "A"}
    updates = [{"message": {"chat": chat}}, {"message": {"chat": chat}}]
    assert len(news_daemon.extract_chats(updates)) == 1


def test_extract_chats_ignores_updates_without_a_chat():
    assert news_daemon.extract_chats([{"update_id": 1}, {"poll": {"id": "x"}}]) == []


def test_extract_chats_handles_missing_names():
    chats = news_daemon.extract_chats([{"message": {"chat": {"id": 7, "type": "private"}}}])
    assert chats[0]["title"] == "(no title)"


def test_get_updates_returns_results(monkeypatch):
    monkeypatch.setattr(
        telegram_client.requests, "get",
        lambda *a, **k: FakeResponse(200, {"ok": True, "result": [{"update_id": 1}]}),
    )
    client = telegram_client.TelegramClient("t", "c")
    assert client.get_updates() == [{"update_id": 1}]


def test_get_updates_raises_on_bad_token(monkeypatch):
    monkeypatch.setattr(
        telegram_client.requests, "get",
        lambda *a, **k: FakeResponse(401, {"ok": False, "description": "Unauthorized"}),
    )
    client = telegram_client.TelegramClient("bad", "c")
    with pytest.raises(telegram_client.TelegramError):
        client.get_updates()


def test_chat_id_optional_for_discovery(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    creds = config.telegram_credentials(require_chat_id=False)
    assert creds["token"] == "token"
    assert creds["chat_id"] == ""


def test_token_still_required_for_discovery(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    with pytest.raises(config.ConfigError):
        config.telegram_credentials(require_chat_id=False)


# ─── quiet hours honour the reader's timezone ────────────────────────────────

def test_quiet_hours_timezone_defaults_to_schedule(cfg):
    cfg["telegram"]["quiet_hours_timezone"] = None
    assert formatter.quiet_hours_timezone(cfg) == cfg["schedule"]["timezone"]


def test_quiet_hours_timezone_override(cfg):
    cfg["telegram"]["quiet_hours_timezone"] = "Europe/Berlin"
    assert formatter.quiet_hours_timezone(cfg) == "Europe/Berlin"


def test_market_morning_is_not_quiet_for_a_gmt_plus_2_reader(cfg):
    """
    09:00 in Berlin is 03:00 in New York. With quiet hours measured in market
    time the reader's morning would arrive silently; measured in their own
    timezone it does not.
    """
    cfg["telegram"]["quiet_hours"] = [22, 7]
    cfg["schedule"]["timezone"] = "America/New_York"
    berlin_morning = datetime(2026, 8, 21, 9, 0, tzinfo=ZoneInfo("Europe/Berlin"))

    cfg["telegram"]["quiet_hours_timezone"] = "America/New_York"
    assert formatter.is_quiet_hour(cfg, berlin_morning.astimezone(ZoneInfo("America/New_York"))) is True

    cfg["telegram"]["quiet_hours_timezone"] = "Europe/Berlin"
    assert formatter.is_quiet_hour(cfg, berlin_morning) is False


def test_shipped_quiet_hours_timezone_is_valid(cfg):
    ZoneInfo(formatter.quiet_hours_timezone(cfg))
