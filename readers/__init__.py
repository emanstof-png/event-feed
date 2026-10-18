"""Readers: one module per way of getting events out of a source.

Each exposes  read(source: dict, window_days=21) -> list[dict]
where source has keys name, url, feed_url, method, rule (for recurring).
Every event dict has: date (YYYY-MM-DD), time (HH:MM or ""), title, venue, link, source.
A reader returns [] and logs when it fails; the caller marks the source.
"""
