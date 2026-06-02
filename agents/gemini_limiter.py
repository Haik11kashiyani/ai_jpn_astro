"""
Shared rate limiter for Google Gemini free tier (single API key).
Keeps calls under per-minute / per-day limits for 12 daily videos.
"""
import os
import time
import logging
import re

# Free tier: ~15 RPM — we target 4/min to leave headroom for token limits
MIN_CALL_INTERVAL = float(os.getenv("GEMINI_MIN_CALL_INTERVAL", "15"))
POST_SUCCESS_COOLDOWN = float(os.getenv("GEMINI_POST_CALL_COOLDOWN", "40"))
MAX_CALLS_PER_MINUTE = int(os.getenv("GEMINI_MAX_CALLS_PER_MINUTE", "4"))
BETWEEN_STEP_COOLDOWN = float(os.getenv("GEMINI_BETWEEN_STEP_COOLDOWN", "35"))

_last_call_ts = 0.0
_minute_window_start = 0.0
_calls_this_minute = 0


def _reset_minute_window_if_needed():
    global _minute_window_start, _calls_this_minute
    now = time.time()
    if now - _minute_window_start >= 60:
        _minute_window_start = now
        _calls_this_minute = 0


def wait_before_call(label: str = "Gemini") -> None:
    """Block until safe to make the next Gemini API request."""
    global _last_call_ts, _calls_this_minute

    _reset_minute_window_if_needed()

    if _calls_this_minute >= MAX_CALLS_PER_MINUTE:
        wait = 60 - (time.time() - _minute_window_start) + 2
        if wait > 0:
            logging.info(
                f"⏱️  {label}: {_calls_this_minute} calls this minute (max {MAX_CALLS_PER_MINUTE}). "
                f"Waiting {wait:.0f}s..."
            )
            time.sleep(wait)
        _reset_minute_window_if_needed()

    elapsed = time.time() - _last_call_ts
    if elapsed < MIN_CALL_INTERVAL:
        wait = MIN_CALL_INTERVAL - elapsed
        logging.info(f"⏱️  {label}: spacing calls — waiting {wait:.1f}s...")
        time.sleep(wait)


def record_call():
    """Record that a Gemini API call was just made."""
    global _last_call_ts, _calls_this_minute
    _last_call_ts = time.time()
    _calls_this_minute += 1


def cooldown_after_success(label: str = "Gemini") -> None:
    """Pause after a successful generation so the next call does not hit RPM limits."""
    logging.info(f"✅ {label}: post-success cooldown {POST_SUCCESS_COOLDOWN:.0f}s...")
    time.sleep(POST_SUCCESS_COOLDOWN)
    record_call()


def wait_between_pipeline_steps(label: str = "pipeline") -> None:
    """Cooldown between major steps in main.py (e.g. almanac → daily script)."""
    logging.info(f"⏳ {label}: inter-step cooldown {BETWEEN_STEP_COOLDOWN:.0f}s...")
    time.sleep(BETWEEN_STEP_COOLDOWN)


def wait_on_rate_limit(error_str: str, label: str = "Gemini") -> int:
    """Wait after a 429; returns seconds waited."""
    parsed = 0
    m = re.search(r"retry in (\d+(?:\.\d+)?)s", error_str, re.I)
    if m:
        parsed = int(float(m.group(1))) + 5
    m = re.search(r'"seconds":\s*(\d+)', error_str)
    if m:
        parsed = max(parsed, int(m.group(1)) + 5)
    wait = max(parsed, MIN_CALL_INTERVAL, 30)
    wait = min(wait, 180)
    logging.info(f"⏳ {label}: 429 rate limit — waiting {wait}s before retry...")
    time.sleep(wait)
    return wait


def is_daily_quota_error(error_str: str) -> bool:
    """True only when the daily quota is exhausted (not a per-minute throttle)."""
    if "PerDay" in error_str or "RequestsPerDay" in error_str:
        return True
    if "limit: 0" in error_str and "PerMinute" not in error_str:
        return True
    return False


def is_rate_limit_error(error_str: str) -> bool:
    return (
        "429" in error_str
        or "rate limit" in error_str.lower()
        or "quota exceeded" in error_str.lower()
        or "Quota exceeded" in error_str
    )
