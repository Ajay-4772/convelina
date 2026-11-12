"""
CONVELINA Privacy-Safe Security Telemetry & Event Monitoring.

Maintains in-memory sliding-window counters for security-sensitive events
(authentication failures, unauthorized access attempts, malicious uploads,
rate limit triggers, prompt-injection flags, OCR failures, AI/DB errors)
without ever storing PII or raw credentials in metrics labels or logs.
"""

from collections import Counter
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List


class SecurityMonitor:
    def __init__(self) -> None:
        self._lock = Lock()
        self._counts: Counter = Counter()
        self._recent_events: List[Dict[str, Any]] = []
        self._max_recent = 100

    def record(self, event_type: str, component: str = "api", outcome: str = "blocked") -> None:
        with self._lock:
            self._counts[event_type] += 1
            self._recent_events.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": event_type,
                "component": component,
                "outcome": outcome,
            })
            if len(self._recent_events) > self._max_recent:
                self._recent_events = self._recent_events[-self._max_recent:]

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "counters": dict(self._counts),
                "recent_events_count": len(self._recent_events),
                "recent_events": list(self._recent_events[-20:]),
            }

    def reset(self) -> None:
        with self._lock:
            self._counts.clear()
            self._recent_events.clear()


_monitor = SecurityMonitor()


def record_security_event(event_type: str, component: str = "api", outcome: str = "blocked") -> None:
    _monitor.record(event_type=event_type, component=component, outcome=outcome)


def get_security_telemetry() -> Dict[str, Any]:
    return _monitor.snapshot()


def reset_security_telemetry() -> None:
    _monitor.reset()

