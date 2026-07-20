"""Rate limit theo IP, cửa sổ trượt, giữ trong tiến trình (TIP-11.1).

Không thêm dependency: một tiến trình một container cho pilot là đủ. Nhiều
worker thì mỗi worker giữ bộ đếm riêng, ghi chú ở đây để khi scale ngang thì
chuyển sang Redis. Hàm check nhận now để test tất định không phụ thuộc đồng hồ.
"""
from collections import defaultdict, deque
from threading import Lock
import time

PER_MINUTE = 10
PER_HOUR = 100


class RateLimiter:
    def __init__(self, per_minute: int = PER_MINUTE, per_hour: int = PER_HOUR):
        self.per_minute = per_minute
        self.per_hour = per_hour
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, now: float | None = None) -> bool:
        """True nếu request được phép và đã ghi nhận, False nếu vượt hạn mức."""
        now = time.time() if now is None else now
        with self._lock:
            dq = self._hits[key]
            hour_cutoff = now - 3600
            while dq and dq[0] < hour_cutoff:
                dq.popleft()
            in_hour = len(dq)
            in_minute = sum(1 for t in dq if t >= now - 60)
            if in_minute >= self.per_minute or in_hour >= self.per_hour:
                return False
            dq.append(now)
            return True


limiter = RateLimiter()
