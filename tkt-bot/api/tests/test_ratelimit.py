"""RateLimiter thuần, không cần DB. now được tiêm để test tất định (TIP-11.1)."""
from app.ratelimit import RateLimiter


def test_minute_limit_blocks_eleventh():
    rl = RateLimiter(per_minute=10, per_hour=100)
    t = 1000.0
    for _ in range(10):
        assert rl.check("ip1", now=t) is True
    # request thứ 11 trong cùng phút bị chặn
    assert rl.check("ip1", now=t) is False


def test_minute_window_slides():
    rl = RateLimiter(per_minute=10, per_hour=100)
    for _ in range(10):
        assert rl.check("ip1", now=1000.0) is True
    assert rl.check("ip1", now=1000.0) is False
    # sau 61 giây, cửa sổ phút trôi qua, lại cho phép
    assert rl.check("ip1", now=1061.0) is True


def test_hour_limit_blocks():
    rl = RateLimiter(per_minute=1000, per_hour=100)
    # rải đều 100 request trong một giờ để không đụng hạn mức phút
    for i in range(100):
        assert rl.check("ip1", now=1000.0 + i * 30) is True
    assert rl.check("ip1", now=1000.0 + 100 * 30) is False


def test_keys_are_isolated():
    rl = RateLimiter(per_minute=10, per_hour=100)
    for _ in range(10):
        assert rl.check("ip1", now=1000.0) is True
    assert rl.check("ip1", now=1000.0) is False
    # IP khác không bị ảnh hưởng
    assert rl.check("ip2", now=1000.0) is True
