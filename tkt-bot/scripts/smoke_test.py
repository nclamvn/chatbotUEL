#!/usr/bin/env python3
"""Smoke test TIP-07: 12 câu chuẩn phủ bốn trạng thái, assert status đúng
và P95 dưới 6 giây khi chưa cache. Chạy: python3 scripts/smoke_test.py [BASE_URL]
"""
import json
import statistics
import sys
import time
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

CASES = [
    # 4 grounded
    ("Điểm chuẩn phân tích dữ liệu 2025?", "grounded"),
    ("Học phí chương trình tiếng Anh năm học 2025-2026?", "grounded"),
    ("Mã tuyển sinh của chuyên ngành phân tích dữ liệu?", "grounded"),
    ("Khoa có những bộ môn nào?", "grounded"),
    # 3 disputed
    ("Trưởng khoa là ai?", "disputed"),
    ("Khoa có bao nhiêu giảng viên cơ hữu?", "disputed"),
    ("Cơ cấu học vị của khoa thế nào?", "disputed"),
    # 3 honest-null
    ("Chỉ tiêu tuyển sinh 2026 là bao nhiêu?", "null"),
    ("Điểm chuẩn năm 2024 của ngành toán kinh tế?", "null"),
    ("Khoa có những loại học bổng gì?", "null"),
    # 2 oos
    ("Nên đầu tư coin nào bây giờ?", "oos"),
    ("Làm hộ bài tập xác suất thống kê được không?", "oos"),
]


def post(path: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f"{BASE}{path}", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main() -> None:
    health = json.load(urllib.request.urlopen(f"{BASE}/health", timeout=10))
    assert health["claims_loaded"] == 121, f"claims_loaded={health['claims_loaded']}"
    print(f"health OK · claims={health['claims_loaded']} · registry={health['registry_version']}")

    failures, times = [], []
    for i, (q, expected) in enumerate(CASES, 1):
        t0 = time.monotonic()
        try:
            # thêm hậu tố phiên để không dính cache của lần chạy trước
            ans = post("/chat", {"message": q, "session_id": f"smoke-{i}"})
            dt = time.monotonic() - t0
            times.append(dt)
            ok = ans["status"] == expected
            if expected in ("grounded", "disputed") and not ans["citations"]:
                ok = False
            mark = "PASS" if ok else "FAIL"
            if not ok:
                failures.append((q, expected, ans["status"]))
            print(f"  {mark} [{ans['status']:9s}] {dt:5.2f}s  {q}")
        except Exception as e:
            failures.append((q, expected, f"lỗi: {e}"))
            print(f"  FAIL [exception] {q}: {e}")

    if times:
        times.sort()
        p95 = times[max(0, int(len(times) * 0.95) - 1)]
        print(f"\nthời gian: median={statistics.median(times):.2f}s · P95={p95:.2f}s (ngưỡng 6s)")
        if p95 >= 6:
            failures.append(("P95", "<6s", f"{p95:.2f}s"))

    if failures:
        print(f"\nSMOKE FAIL: {len(failures)} lỗi")
        for q, exp, got in failures:
            print(f"  - {q}: kỳ vọng {exp}, nhận {got}")
        sys.exit(1)
    print(f"\nSMOKE PASS: {len(CASES)}/12 đúng trạng thái, P95 đạt")


if __name__ == "__main__":
    main()
