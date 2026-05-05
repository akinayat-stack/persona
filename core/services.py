from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests
from django.conf import settings


@dataclass
class QuoteResult:
    text: str | None
    author: str | None
    error: str | None = None


def fetch_daily_quote(timeout: int = 4) -> QuoteResult:
    """Fetch a quote from a public API and return resilient payload for UI rendering."""
    url = getattr(settings, 'QUOTE_API_URL', 'https://zenquotes.io/api/random')
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        data: Any = response.json()
        if isinstance(data, list) and data:
            item = data[0]
            return QuoteResult(text=item.get('q'), author=item.get('a'))
        if isinstance(data, dict):
            return QuoteResult(text=data.get('content') or data.get('q'), author=data.get('author') or data.get('a'))
        return QuoteResult(text=None, author=None, error='Invalid quote payload format.')
    except requests.RequestException:
        return QuoteResult(text=None, author=None, error='Unable to load quote service right now.')
