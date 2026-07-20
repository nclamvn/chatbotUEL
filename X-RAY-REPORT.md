# X-RAY · Báo cáo toàn diện dự án TKT-BOT

> Chatbot tuyển sinh Khoa Toán Kinh tế UEL · "trustworthy RAG" có trích dẫn truy vết
> Ngày quét: 2026-07-20 · Nhánh: `main` · Commit đầu: `60e5a53` (Registry v1.1)
> Phạm vi quét: toàn repo trừ `node_modules`, `.git`, `.next`

---

## 0. TL;DR (một phút đọc)

- **Bản chất**: hệ hỏi đáp có căn cứ (grounded Q&A) cho tuyển sinh + thông tin nhân sự Khoa Toán Kinh tế UEL. Triết lý cốt lõi: **mọi con số và tên riêng trong câu trả lời phải truy vết được về một `claim` có `evidence_span` nguyên văn từ nguồn**. Không có nguồn thì thà nói "chưa có dữ liệu" chứ không bịa.
- **Ba khối**:
  1. `toan_kinh_te_uel/` — data refinery offline: HTML snapshot → 110 claims có kiểm định (23 thực thể, 14 gate chất lượng).
  2. `tkt-bot/api/` — FastAPI (Python 3.12): router → retrieval hybrid → composer (Claude) → verifier (trace + style) → vòng viết lại → finalize.
  3. `tkt-bot/web/` — Next.js 15 + React 19: UI chat mobile-first có citation chip, evidence sheet, khối disputed/null, dark mode.
- **Trạng thái**: **7/7 TIP đã DONE**, 4 container (db, api, web, caddy) dựng lại bằng một lệnh. `pytest` xanh, smoke 12/12, Lighthouse a11y 100.
- **Chặn duy nhất trước go-live thật**:
  1. **Chưa có `ANTHROPIC_API_KEY`** → toàn bộ bằng chứng hiện tại chạy trên đường **fallback deterministic** (template), chưa từng chạy LLM thật. TIP-08 đã soạn sẵn, chờ key để thi hành.
  2. **Chưa xác nhận dữ liệu nhân sự** với văn phòng Khoa (`khoatkt@uel.edu.vn`) — điều kiện go-live treo trong Decisions Log.
- **Rủi ro cần chốt**: production **bắt buộc `EMBEDDINGS=e5`** (hiện mặc định `hash` chỉ hợp dev); 5 ô dữ liệu đang **disputed** cần người xác nhận; chưa có rate limiting.

---

## 1. Bản đồ kiến trúc

```
┌─────────────────────── toan_kinh_te_uel/ (OFFLINE, ngoài runtime) ──────────────────────┐
│  snapshots/*.html  →  refinery.py (7 stage + auditor, 14 gate)  →  claims.jsonl (110)     │
│                       bites.py (14 bài test cho từng gate)          registry_output.txt   │
└───────────────────────────────────────┬───────────────────────────────────────────────────┘
                                         │  copy byte-for-byte
                                         ▼
┌───────────────────────────────── tkt-bot/ (RUNTIME, docker compose) ─────────────────────┐
│                                                                                            │
│   caddy :8080  ──/api/*──►  api :8000 (FastAPI)  ──►  db :5433 (postgres + pgvector)       │
│         │                        │                                                         │
│         └──/*──►  web :3002 (Next.js 15)                                                    │
│                                                                                            │
│   Luồng /chat:  router → retrieval(registry + BM25 + pgvector + RRF) → composer(Claude)    │
│                 → verifier(trace số/tên + style_lint) → [vòng viết lại ≤2] → finalize      │
└────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Contract trả lời** (mọi tầng tuân theo, khóa trong Blueprint):
```json
{
  "answer_markdown": "...",
  "status": "grounded | disputed | null | oos",
  "citations": [{"claim_id","source","tier":"A|B|C","fetched_at","evidence_span","url"}],
  "followups": ["...", "...", "..."]
}
```

---

## 2. Khối DATA — `toan_kinh_te_uel/` (data refinery)

**Vai trò**: pipeline offline biến HTML thô thành tri thức có kiểm định. Không nằm trong runtime của bot; sản phẩm (`claims.jsonl`) được copy sang `tkt-bot/api/data/`.

### 2.1 Con số chốt (Registry v1.1)
- **110 claims** (từ 71 ở v1.0), **23 thực thể** (từ 11): 1 khoa, 1 trường, 1 ngành, 3 chuyên ngành, 17 nhân sự.
- **Coverage 100%** (23/23 thực thể trong universe). Build digest idempotent, auditor OK, **0 gate bites**.
- **35 field schema**; 34/35 có dữ liệu (`website` = 0 claim).
- **5 ô disputed** (cần người xác nhận — xem 7.2).

### 2.2 Mô hình claim
```json
{
  "entity": "Khoa Toán Kinh tế",
  "field": "nam_len_khoa",
  "value": "2019",
  "evidence_span": "Năm 2019 Bộ môn được nâng cấp thành Khoa Toán Kinh tế",
  "extraction": "verbatim | normalized | inferred",
  "tier": "A | B | C",
  "capture": {"url","fetched_at","snapshot","source"}
}
```
- **Tier**: A = nguồn chính chủ (`maths.uel.edu.vn`, ~69% claim), B = báo chí/thứ cấp (`plo.vn`, `tuoitre.vn`, ~6%), C = tổng hợp (`tuyensinh247.com`, ~15% — chủ yếu điểm chuẩn).
- **Extraction**: verbatim (chép nguyên), normalized (chuẩn hóa nhẹ), inferred (suy ra — ~24% claim, chủ yếu field `loai`).

### 2.3 Pipeline `refinery.py` (435 dòng) — 7 stage + auditor
1. **Per-claim gates**: `SOURCED_ATTR` (tier/field hợp lệ), `CAPTURE_MISSING` (file snapshot tồn tại), `SPAN_NOT_FOUND` (evidence_span là substring của snapshot sau khi normalize HTML entity + NFC).
2. **Canonicalize**: áp `alias_map` (vd "UEL" → tên đầy đủ); `AMBIGUOUS_MERGE_UNFLAGGED` chặn gộp nhầm các cluster mơ hồ.
3. **Build registry**: gom theo entity→field, hòa giải xung đột → trạng thái `corroborated` (≥2 nguồn A/B độc lập cùng giá trị) / `sourced` / `disputed` (nhiều giá trị khác nhau) / `null`.
4. **Domain gates** (tùy chọn, domain này không dùng): origin-evidence, no-inferred, incident-grounding, required-fields...
5. **Aggregates**: coverage %, rollup theo `loai`; `DISTRIBUTION_NO_DENOMINATOR` bắt buộc có mẫu số.
6. **Auditor**: tái dựng độc lập để bắt bug builder.
7. **Idempotence**: build 2 lần, so digest — lệch là fail `IDEMPOTENT`.

### 2.4 `bites.py` (279 dòng) — QA cho chính các gate
14 bài test kiểu "tiêm lỗi rồi kiểm gate có bắt không" (xóa snapshot, bịa evidence_span, set tier bậy, phá idempotence...). Triết lý: *"một gate không được test là một gate sẽ cắn ở production"*.

### 2.5 14 snapshot nguồn
`maths.uel.edu.vn` (8 file: home, lịch sử, nhân sự, sơ đồ, tầm nhìn, CTĐT, công bố, định hướng NC) · `tuyensinh.uel.edu.vn` (2) · `uel.edu.vn` (1) · `tuyensinh247.com` (2, điểm chuẩn) · `plo.vn`/`hocmai` (báo chí + hướng nghiệp).

---

## 3. Khối API — `tkt-bot/api/` (FastAPI, Python 3.12)

**~1.900 dòng**, tách module rõ. Luồng một request `/chat`:

```
router.classify() → [cache check nếu factual] → retrieval.retrieve()
  → composer.compose() → verifier.verify() → [rewrite ≤2 nếu fail] → composer.finalize()
  → telemetry.log + cache_put → Answer JSON
```

### 3.1 Module chính
| File | Vai trò |
|---|---|
| `main.py` | Endpoints: `/health`, `/chat`, `/chat/stream` (SSE), `/telemetry`, `/telemetry/nulls`, `/telemetry/stats`. CORS mở `*`. |
| `router.py` | Phân loại intent `factual\|interpretive\|oos\|smalltalk`. Có key → Claude Haiku few-shot; không key → heuristic regex. |
| `retrieval.py` | 3 đường: **structured lookup** (registry cell theo entity+field, person-name lookup 17 nhân sự, year check), **BM25** (rank-bm25), **pgvector** (L2 distance). Hợp nhất bằng **RRF** (K=60), tie-break theo tier. Số (điểm, chỉ tiêu) **không** đi qua vector. |
| `composer.py` | Sinh câu. Có key → Claude Sonnet 4.6 + system prompt = Constitution, max 1200 token, output JSON. Không key → template deterministic. `finalize()` **dựng lại citation từ DB**, không tin metadata của LLM. |
| `constitution.py` | Domain Constitution: STYLE_RULES (6 luật văn phong), BEHAVIOR_RULES, OUTPUT_CONTRACT, SYNONYMS, disclaimer. |
| `verifier.py` | 2 tầng: **trace** (mọi số phải khớp value+evidence_span+chunk+câu hỏi; mọi tên riêng phải có trong context) + **style_lint**. Trả feedback để composer viết lại. |
| `style_lint.py` | Hàm thuần, không DB/LLM. Cứng: `EMDASH`, `SEMICOLON` (>1), `COMMA_VA` (phẩy trước "và"). Mềm: `REPEAT` (lặp từ >2 lần/đoạn, gợi ý đồng nghĩa). |
| `pipeline.py` | Điều phối; `MAX_REWRITES=2`; hết vòng → `SAFE_FALLBACK` status null. |
| `embeddings.py` | `hash` (tất định offline 384-dim, dev) hoặc `e5` (`multilingual-e5-small` qua fastembed, production). |
| `db.py` | Postgres + pgvector. Bảng: `claims`, `registry_cells`, `chunks`, `meta`, `telemetry_events`, `answer_cache`. |
| `telemetry.py` | Cache 24h theo câu chuẩn hóa (tự vô hiệu khi `registry_version` đổi), log ẩn danh (hash session), counter LLM, null backlog. |

### 3.2 Cơ chế an toàn nổi bật
- **Trace gate REQ-07/L2 fix**: allowed tách hai tập — số chỉ đối chiếu value+evidence_span+chunk; tên nguồn/snapshot chỉ phục vụ trace tên riêng; số dính trong tên nguồn (vd "247") bị mask trước khi bóc → LLM bịa "247" rời vẫn bị chặn.
- **Style gate REQ-06**: vi phạm cứng → composer nhận feedback viết lại (≤2 vòng) → hết thì fallback an toàn kèm log.
- **SSE stream sau khi verifier duyệt** (không stream token thô từ LLM) vì style gate phải chạy trước render.

### 3.3 Test (`pytest`, chạy trong container python:3.12)
- `test_style_lint` (20), `test_verifier` (7), `test_ingest` (2), `test_pipeline` (2, monkeypatch vòng viết lại), `test_retrieval_v11` (5, cần DB v1.1). Tổng ~28-36 tùy đợt.
- **Chưa test**: endpoint HTTP `/chat` end-to-end, SSE flow, hành vi cache TTL, đường LLM thật (đang mock).

---

## 4. Khối WEB — `tkt-bot/web/` (Next.js 15 + React 19)

Stack: Next 15.1 App Router, React 19, TypeScript strict, **CSS Modules thuần** (không Tailwind/UI lib), font Be Vietnam Pro, Node 22 Alpine standalone.

### 4.1 Kiến trúc component
```
ChatSurface (orchestrator: messages[], busy, sheetCitation)
├── ModeToggle (dark mode, localStorage "tkt-theme")
├── SeasonCards (4 thẻ mùa ở màn chào — REQ-09)
├── MessageBubble[]
│   ├── renderMarkdown (bold, list, paragraph — tối giản)
│   ├── grounded → CitationChip[]   disputed → DisputedBlock   null/oos → NullBlock
│   └── followups (≤3)
├── InputBar
└── EvidenceSheet (mobile: bottom sheet · ≥1100px: panel phải 380px đẩy cột chat)
```

### 4.2 Giao tiếp API — `lib/api.ts`
- `POST /api/chat/stream`, đọc **SSE tự parse** (`event: partial` cập nhật text sống, `event: answer` payload đầy đủ).
- `next.config.ts` rewrite `/api/*` → `API_PROXY_URL` (dev: `localhost:8000`, docker: `api:8000`, prod: Caddy). Không hardcode URL tuyệt đối trong standalone build.

### 4.3 UX "trustworthy RAG"
- **grounded**: markdown + chip trích dẫn.
- **disputed**: khối vàng "Nguồn chưa thống nhất", liệt kê mọi phiên bản kèm nguồn·tier, khuyên xác nhận với văn phòng Khoa.
- **null**: "Khoa chưa công bố" + mailto `khoatkt@uel.edu.vn`. **oos**: "Ngoài phạm vi hỗ trợ" + kênh đúng.
- **EvidenceSheet**: đoạn gốc nguyên văn (highlight số), tier, ngày chụp, URL, claim_id; Esc đóng, focus trả về chip.
- Responsive: <900px vỏ điện thoại giữ nguyên pixel · ≥900px bỏ vỏ, cột 760px căn giữa · ≥1100px evidence thành panel phải.

---

## 5. Hạ tầng & triển khai

- **docker-compose**: `db` (pgvector/pgvector:pg16, host **5433**), `api` (build ./api, :8000), `web` (build ./web, host **3002**), `caddy` (:**8080**, reverse proxy `/api/*`→api, `/*`→web). Volume `tkt_pgdata`, `tkt_caddy_data`.
- **Port lệch chuẩn** (5433/3002/8080) vì 5432/3000 đã bị dự án khác trên máy chiếm (rtr-mrp-db, một app node).
- **`.env`**: `ANTHROPIC_API_KEY` (trống → fallback), `COMPOSER_MODEL=claude-sonnet-4-6`, `EMBEDDINGS=hash`, `POSTGRES_PASSWORD`, `HTTP_PORT`, `SITE_ADDRESS` (Caddy tự lo TLS khi có domain).
- Dựng lại từ máy sạch: `docker compose up -d --build` (một lệnh).

---

## 6. Trạng thái dự án & việc treo

### 6.1 Đã xong (COMPLETION-REPORT)
7/7 TIP DONE. Bằng chứng: loader idempotent, ô disputed mẫu đúng, ingest đúng 14 snapshot (235 chunks), structured-trước-semantic, composer 4 AC pass, style_lint 20/20, trace verifier chặn số/tên ngoài context, UI 360px không tràn, disputed render, bottom sheet, dark mode persist, **Lighthouse a11y 100/100**, cache counter (composer_calls đứng yên khi cache hit), null backlog, smoke 12/12, volume persistence.

### 6.2 TIP-08 đã soạn, **chờ API key** để thi hành
Bốn+một đầu việc: (0) L2 trace fix — **đã làm**; (1) điền key, xác nhận model id thật; (2) smoke 12 câu qua LLM đo **P95 thật ngưỡng 6s**; (3) 30 câu style eval với style_lint làm trọng tài (`eval-questions.txt` có sẵn); (4) bật `e5`, re-ingest, so hash vs e5 trên 10 câu diễn giải; (5) liếc reflow 1100-1200px khi SSE stream lúc panel mở.

### 6.3 Điều kiện go-live còn treo
1. **API key** (Open Question 2) — chưa cấp. Khuyến nghị Blueprint: key riêng dự án, đặt spend limit + usage alert ngay từ đầu (mùa tư vấn lưu lượng tăng đột ngột theo ngày công bố điểm).
2. **Xác nhận dữ liệu nhân sự** với `khoatkt@uel.edu.vn` — bắt buộc trước khi mở cho người dùng thật.
3. **Nơi deploy** (Open Question 1) — đề xuất Render cho pilot, tách khỏi hạ tầng RTR nội bộ.

---

## 7. Rủi ro, nợ kỹ thuật, khoảng trống

### 7.1 Rủi ro mức cao
- **Chưa có bằng chứng đường LLM thật**: P95 0.08s của smoke là số của fallback template, **không dự báo được production**. Fallback pass style gate vì chính nó là template. Phải chạy TIP-08 mới đóng được D1/D2.
- **Production bắt buộc `e5`** nhưng mặc định là `hash`: nếu deploy quên đổi env, chất lượng retrieval ngữ nghĩa tiếng Việt sẽ kém (hash chỉ hợp dev, corpus pilot 14 tài liệu BM25 gánh chính).
- **Không rate limiting**: CORS `*`, không throttle → rủi ro DoS nếu phơi công khai. Mùa cao điểm dễ đội chi phí LLM.

### 7.2 Năm ô disputed cần người chốt
| Ô | Xung đột |
|---|---|
| `so_giang_vien_co_huu` (Khoa) | 14 vs 15 |
| `co_cau_hoc_vi` (Khoa) | 03 PGS.TS/08 TS/**03** ThS vs **04** ThS |
| `hoc_ham_hoc_vi` — Phạm Hoàng Uyên | PGS.TS vs TS |
| `dia_chi` (Trường) | hai định dạng (Quốc lộ 1 vs Đỗ Mười) |
| `hoc_ham_hoc_vi` — Trần Nguyễn Hoàng Sang | ThS vs CN |

Tất cả low-frequency, bot sẽ hiện khối DISPUTED khi bị hỏi — không chặn chức năng lõi, nhưng nên xác nhận cùng lần rà nhân sự với văn phòng Khoa.

### 7.3 Nợ kỹ thuật đáng ghi
- **Soft warning (REPEAT) không tới người dùng**: pipeline log nhưng client không thấy.
- **SSE parse thủ công bằng regex** ở web (không dùng lib) — rủi ro nếu backend gửi SSE méo; chưa có React Error Boundary.
- **Không có multi-turn**: mỗi request độc lập, session_id chỉ hash để log, followups generic.
- **BM25 `@lru_cache` không tự vô hiệu** khi bảng chunks đổi giữa chừng.
- **Log bằng `print()`**, chưa structured logging; khó truy vết request-id xuyên component.
- **`website` field 0 claim**: hoặc bỏ field hoặc xác nhận Khoa không có site riêng.
- **Snapshot lưu HTML thô**: nếu nguồn đổi layout, evidence_span có thể mất khớp (chưa có scheduler phát hiện staleness; `refresh_days` chỉ mang tính khuyến nghị).

---

## 8. Điểm mạnh nổi bật

1. **Grounding thật sự**: trace gate đảm bảo không bịa số/tên; disputed hiện mọi phiên bản thay vì gộp mất mát; null thành thật thay vì ảo giác.
2. **Fallback offline hoàn chỉnh**: không key vẫn chạy đủ 4 intent (heuristic router + template composer) — hạ rào phụ thuộc API.
3. **Audit trail nghiêm**: 14 gate + bites test + auditor + idempotence digest; mọi claim có nguồn/tier/ngày/evidence.
4. **Contract sạch**: Pydantic khóa schema; finalize dựng lại citation từ DB chống LLM tiêm metadata.
5. **UI trust-first, a11y 100**: citation chip → evidence sheet, tier badge, dark mode hạng nhất, responsive 3 mốc, focus management, reduced-motion.
6. **Kỷ luật quy trình**: Blueprint là khế ước, Requirements Matrix REQ-01..14, Decisions Log ghi mọi deviation kèm lý do — hiếm thấy ở dự án quy mô này.

---

## 9. Khuyến nghị ưu tiên

**Trước go-live (bắt buộc):**
1. Cấp `ANTHROPIC_API_KEY` (key riêng + spend limit + usage alert) → chạy **TIP-08** đóng D1/D2/D3, lấy P95 thật và bằng chứng văn phong LLM.
2. Set `EMBEDDINGS=e5` cho production, re-ingest, xác nhận ingest sạch 235 chunks.
3. Rà + xác nhận dữ liệu nhân sự với `khoatkt@uel.edu.vn`, chốt 5 ô disputed.

**Nên làm sớm (hardening):**
4. Thêm rate limiting + giới hạn độ dài câu hỏi trước khi phơi công khai.
5. Structured logging + request-id; React Error Boundary bọc ChatSurface.
6. Nối `/telemetry/nulls` vào vòng crawl bổ sung của refinery (vòng kín dữ liệu).

**Phase 2:**
7. Giao diện tiếng Anh; multi-turn context; scheduler phát hiện snapshot lệch nguồn.

---

## Phụ lục · Chỉ số nhanh
- Tổng file (trừ node_modules/.git): ~9.361 · Dung lượng repo: ~428 MB (phần lớn là snapshots + node_modules).
- API: ~1.900 dòng Python, 6 bảng Postgres. Web: ~28 file, không UI lib. Refinery: 435 (refinery) + 279 (bites) dòng.
- Claims: 110 · Thực thể: 23 · Snapshot: 14 · Chunks tầng 2: 235 · Field schema: 35.
- Model: composer `claude-sonnet-4-6`, router `claude-haiku-4-5-20251001`.
- Git: 3 commit (`cbaf382` TIP-01→07 + desktop, `ca1c3f6` TIP-08 đầu việc 5, `60e5a53` Registry v1.1).

*Báo cáo do Claude Code lập từ quét tĩnh mã nguồn + tài liệu dự án, không chỉnh sửa file nào.*
