# BLUEPRINT — Cổng hỏi đáp Khoa Toán Kinh tế UEL
## Vibecode Kit v6.1 · Chủ thầu soạn · chờ Human APPROVED

Project code: TKT-BOT. Ngày: 12/07/2026.
Trạng thái: DRAFT chờ approve. Blueprint là khế ước. Sau approve muốn đổi kiến trúc thì quay lại Vision.

---

## 1. SCAN (rút gọn, project mới)

Folder trống. Tài sản mang vào từ phiên trước: domain refinery `toan_kinh_te_uel` gồm 71 claims đã qua 6 gate, 13 snapshot nguồn, registry output. Engine refinery giữ nguyên vai trò pipeline dữ liệu offline, không nằm trong runtime của bot.

## 2. Requirements Matrix

| REQ-ID | Yêu cầu | Nguồn quyết định |
|---|---|---|
| REQ-01 | Mọi con số và tên riêng trong câu trả lời truy vết được về claim có evidence_span | Nguyên lý CCG-RAG, phiên 12/07 |
| REQ-02 | Ba trạng thái trả lời grounded, disputed, honest-null hiển thị khác nhau rõ ràng | Blueprint v1.0 |
| REQ-03 | Citation chip mở bottom sheet chứa đoạn gốc nguyên văn, tier, ngày chụp, URL | Mockup đã duyệt |
| REQ-04 | Retrieval hybrid: BM25 cộng vector, lọc theo authority tier, factual ưu tiên registry lookup | Blueprint v1.0 |
| REQ-05 | Văn phong người: cấm em-dash, hạn chế chấm phẩy, không phẩy trước "và", chống lặp từ, ưu tiên đồng nghĩa, technical terms giữ tiếng Anh | Human, phiên này |
| REQ-06 | Style gate tự động lint REQ-05 trước khi render, vi phạm thì composer viết lại | Chủ thầu đề xuất |
| REQ-07 | Verifier chặn câu trả lời chứa số không truy vết được | Blueprint v1.0 |
| REQ-08 | UI mobile-first theo mockup: Be Vietnam Pro, accent #144e8c, dark mode hạng nhất, WCAG AA | Mockup đã duyệt |
| REQ-09 | Bốn thẻ câu hỏi theo mùa ở màn hình chào, followups tối đa ba | Mockup đã duyệt |
| REQ-10 | Câu hỏi ngoài phạm vi bị từ chối lịch sự kèm kênh đúng | Blueprint v1.0 |
| REQ-11 | Telemetry ẩn danh, câu honest-null lặp lại thành backlog crawl | Blueprint v1.0 |
| REQ-12 | Cache câu hỏi phổ biến để giảm chi phí LLM | Blueprint v1.0 |
| REQ-13 | Disclaimer cố định và luật không tư vấn vượt thẩm quyền | Blueprint v1.0 |
| REQ-14 | Deploy Docker Compose sau Caddy, một lệnh dựng lại được | Hạ tầng chuẩn RTR |

## 3. Kiến trúc

Hai service trong một compose.

```
tkt-bot/
├── api/                      # FastAPI (Python 3.12)
│   ├── app/
│   │   ├── main.py           # routes: /chat, /health, /telemetry
│   │   ├── router.py         # intent: factual | interpretive | oos | smalltalk
│   │   ├── retrieval.py      # registry lookup + BM25 + pgvector + RRF + tier filter
│   │   ├── composer.py       # Claude API, JSON contract
│   │   ├── verifier.py       # trace numbers/names + style_lint
│   │   ├── style_lint.py     # REQ-05 rules, pure function, test được độc lập
│   │   ├── constitution.py   # system prompt = Domain Constitution
│   │   ├── models.py         # Pydantic: Claim, Chunk, Answer, Citation
│   │   └── telemetry.py
│   ├── data/
│   │   ├── claims.jsonl      # copy từ domain refinery, read-only
│   │   ├── registry.json     # build tất định từ claims (loader sinh)
│   │   └── chunks/           # corpus tầng 2, mỗi chunk kèm metadata nguồn
│   └── scripts/load_data.py  # nạp Postgres + pgvector, idempotent
├── web/                      # Next.js 15, TypeScript, App Router
│   └── app/, components/     # ChatSurface, CitationChip, EvidenceSheet,
│                             # DisputedBlock, NullBlock, SeasonCards, InputBar
├── docker-compose.yml        # api + web + postgres(pgvector)
└── Caddyfile
```

Hợp đồng trả lời, mọi tầng tuân theo:

```json
{
  "answer_markdown": "...",
  "status": "grounded | disputed | null | oos",
  "citations": [{"claim_id": "...", "source": "...", "tier": "A", "fetched_at": "...", "evidence_span": "...", "url": "..."}],
  "followups": ["...", "...", "..."]
}
```

## 4. Domain Constitution (trích phần văn phong, REQ-05)

Bot xưng "mình", gọi người dùng là "bạn". Câu ngắn, chủ động, tự nhiên như người thật. Các luật cứng:

1. Cấm ký tự em-dash và en-dash trong câu trả lời. Cần ngắt ý thì dùng dấu phẩy hoặc tách thành câu mới.
2. Dấu chấm phẩy chỉ được xuất hiện tối đa một lần trong một câu trả lời và chỉ khi liệt kê phức tạp.
3. Không đặt dấu phẩy ngay trước chữ "và".
4. Không lặp một từ nội dung quá hai lần trong một đoạn. Dùng từ đồng nghĩa: điểm chuẩn, mức trúng tuyển, ngưỡng đầu vào. Khoa, đơn vị. Sinh viên, người học, bạn.
5. Technical terms giữ tiếng Anh: claim, tier, snapshot, dark mode.
6. Không mở đầu bằng "Dựa trên dữ liệu" hay "Theo thông tin tôi có". Vào thẳng câu trả lời, nguồn đã có chip lo.

Style gate (REQ-06) lint máy các luật 1, 2, 3 và cảnh báo luật 4 bằng đếm tần suất từ đã chuẩn hóa dấu. Vi phạm cứng thì composer nhận lỗi và viết lại, tối đa hai vòng, quá hai vòng trả lời fallback an toàn kèm log.

## 5. Design system (REQ-08)

Token lấy nguyên từ mockup đã duyệt: paper #fbfaf7, ink #181a1f, accent #144e8c, hairline #e6e3db, bộ dark tương ứng. Font Be Vietnam Pro bốn trọng lượng. Bo góc 16px cho bubble, 999px cho chip. Tier badge A xanh đậm, B xám xanh, C xám. Khối disputed nền vàng nhạt, khối honest-null nền trung tính. Motion dưới 200ms, tôn trọng prefers-reduced-motion.

## 6. Task Graph

```
TIP-01 Scaffold + data loader ──► TIP-02 Retrieval ──► TIP-03 Composer + Constitution
                                                            │
                                        TIP-04 Verifier + style_lint ◄┘
TIP-05 Frontend (song song từ sau TIP-01, mock API trước)
TIP-06 Telemetry + cache (sau TIP-03)
TIP-07 Deploy + smoke test (cuối)
```

P0: TIP-01, 02, 03, 04, 05. P1: TIP-06, 07.

## 7. Checkpoints

Blueprint approval (bây giờ). Design review nhanh sau TIP-05 vì UI là mặt tiền của dự án. Verify report trước khi ship. RRI results review bỏ qua vì requirements đã đóng qua ba phiên trước, lý do ghi tại đây theo luật sàn audit trail.

## 8. Open Questions cho Human (mode CHALLENGE, trả lời nhanh được)

1. Deploy ở đâu: VPS 171.244.40.23 subdomain mới hay Render? Đề xuất Render cho pilot vì tách khỏi hạ tầng RTR nội bộ.
2. Anthropic API key dùng key riêng cho dự án này? Đề xuất có, giới hạn spend riêng.
3. Ngôn ngữ giao diện: chỉ tiếng Việt cho pilot? Đề xuất có, tiếng Anh để Phase 2.
4. Corpus tầng 2 pilot lấy đúng 14 snapshot được claims tham chiếu? Đề xuất có. (Sửa từ "13" theo Amendment 2026-07-12, xem Decisions Log.)
5. Tên hiển thị của bot? Đề xuất "Trợ lý Khoa Toán Kinh tế", không đặt tên người.

Human gõ APPROVED kèm câu trả lời nào muốn sửa. Sau đó Chủ thầu phát TIP-01 cho Thợ.

## 9. Decisions Log

**2026-07-12 · Amendment TIP-02 (Chủ nhà chốt sau kiểm tra bàn giao).** Corpus tầng 2 ingest đúng 14 snapshot được claims tham chiếu, không phải 13 như bản draft. Lý do lệch: đếm trước khi rà lại tham chiếu. File placeholder lỗi fetch và bản chụp thừa bị loại ngay ở bước liệt kê nguồn. Assert bổ sung: file dưới 1 KB hoặc không xuất hiện trong bất kỳ capture.snapshot nào thì ingest bỏ qua và log tên. Không đổi kiến trúc, ràng buộc acceptance giữ nguyên 71 claims và 11 entities.

**2026-07-12 · Ghi chú câu hỏi (2).** Nếu duyệt key riêng thì đặt spend limit ngay từ ngày đầu và bật usage alert, vì mùa tư vấn tuyển sinh lưu lượng tăng đột ngột theo ngày công bố điểm.

**2026-07-12 · Điều kiện go-live (không chặn TIP-01 đến TIP-07).** Xác nhận dữ liệu nhân sự với văn phòng Khoa (khoatkt@uel.edu.vn) phải xong trước khi mở cho người dùng thật.

**2026-07-12 · Thiếu sót Chủ thầu, deviation Thợ adopt nguyên trạng.** File eval-questions.txt "kèm TIP-08" được hứa trong khế ước nhưng không đính. Thợ soạn thay 30 câu và ghi chú nguồn ngay đầu file. Thiếu sót thuộc Chủ thầu.

**2026-07-12 · L2 trả lời trước, thành mục 0 của TIP-08.** Fix nới allowed text của trace verifier sang tên nguồn và snapshot (chữa ca "247" bóc oan) mở khe ngược: số nằm trong tên nguồn thành hợp lệ với mọi câu được cấp nguồn đó, LLM bịa "247" rời sẽ lọt. Chốt: tách allowed thành hai tập, số chỉ đối chiếu value cộng evidence_span (và text chunk, vốn là evidence tầng 2), tên nguồn với snapshot chỉ phục vụ trace tên riêng; số dính trong tên nguồn được mask trước khi bóc. Kèm unit test: "247" đứng rời khi context không có claim mang giá trị ấy phải bị chặn. Fix word boundary của style_lint duyệt thẳng, ca "khoatkt" vào bộ hồi quy vĩnh viễn.

**2026-07-12 · Mở rộng REQ-08 sang desktop (Human chốt ba quyết định).** Web responsive không Electron; ≥900px bỏ vỏ điện thoại, cột hội thoại 760px căn giữa; ≥1100px evidence thành panel phải 380px đẩy cột chat, kèm nút đóng, phím Esc và focus trả về chip. Mobile và phone-shell (dưới 900px) giữ nguyên pixel, token màu không đổi, chỉ thêm hai token layout --chat-max và --panel-w. Verify: ma trận 360/480/768/900/1024/1100/1440/1920 không tràn ngang, cột luôn 760, morph qua mốc 1100 không kẹt, Lighthouse a11y 100 cả mobile lẫn desktop.

**2026-07-12 · VERIFY vòng 1: READY-với-deferred (D1 đến D5).** Chủ thầu chấp nhận cả năm deviation của Thợ. Deviation embedding hash tất định được adopt cho dev và nâng thành điều kiện D3: production bắt buộc `EMBEDDINGS=e5` (multilingual-e5-small), hash chỉ dùng dev/test. D1 (bằng chứng đường LLM thật) chờ API key, xử lý bằng TIP-08 gồm bốn đầu việc: smoke 12 câu qua LLM đo P95 ngưỡng 6s, bộ 30 câu đánh giá văn phong với style_lint làm trọng tài, bật e5 so sánh retrieval trên 10 câu diễn giải, xuất bằng chứng cache counter. D4 đã đóng ngay vòng này bằng bằng chứng counter trong COMPLETION-REPORT.md của repo.
