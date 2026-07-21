# X-Ray Codebase — TKT-BOT (Chatbot Khoa Toán Kinh tế UEL)

> Chụp ngày **21/07/2026** · HEAD `b7ea693` · registry digest `a3ea65c1` · 139 claims.
> Số liệu **đo sống** từ cây mã (đã loại `node_modules`, `.next`).

---

## 1. Tổng quan số

| Hạng mục | Giá trị |
|---|---|
| Mã production Python (app + engine) | **2.495 LOC** |
| Mã production Frontend (TS/TSX, không CSS) | **943 LOC** |
| CSS (module + global) | ~1.000 LOC |
| Test (Python) | **529 LOC · 58 hàm test · 9 file** |
| Script vận hành/eval (Python) | 541 LOC |
| Tổng lịch sử git | 17 commit · từ 12/07/2026 · 1 tác giả (nclamvn) |
| Corpus bằng chứng | 41 snapshot · 6.9 MB · `claims.jsonl` 68 KB |

**Đặc điểm:** codebase **nhỏ và đặc** — dưới 3.5K LOC logic gánh một hệ RAG có kỷ luật bằng chứng đầy đủ. Không phình, không framework thừa.

---

## 2. Ngăn xếp công nghệ (đầy đủ version)

### Backend — Python 3.12-slim
| Thư viện | Version | Vai trò |
|---|---|---|
| FastAPI | 0.115.* | HTTP API, dependency injection |
| Uvicorn[standard] | 0.32.* | ASGI server |
| psycopg[binary] | 3.2.* | Driver Postgres (psycopg3) |
| Pydantic | 2.* | Contract/validation |
| **anthropic** | 0.40.* | Claude composer (gate sau key) |
| **rank-bm25** | 0.2.* | Sparse retrieval BM25 |
| **fastembed** | 0.4.* | Embedding ONNX (multilingual-e5-small, không cần torch) |
| beautifulsoup4 + lxml | 4.12 / 5.* | Parse HTML snapshot lúc ingest |
| PyYAML | 6.* | domain.yaml (schema/config) |
| pytest + httpx | 8.* / 0.27.* | Test |

### Frontend — Node 22-alpine (multi-stage: deps → build → runner)
| | Version |
|---|---|
| Next.js | 15.1 (App Router) |
| React | 19.0 |
| TypeScript | 5.* |

### Hạ tầng
Postgres **16 + pgvector** · Caddy **2** (reverse proxy + basic-auth gate) · Docker Compose (4 service) · Render blueprint (`render.yaml`) sẵn.

---

## 3. Kiến trúc & luồng dữ liệu

```
                    ┌─────────── OFFLINE: tinh lọc dữ liệu ───────────┐
   nguồn web/CV ──> snapshots/ (raw) ──> refinery.py (7+ cổng fail-loud)
                                             │  build tất định + auditor
                                             ▼
                                       claims.jsonl (139, digest a3ea65c1)
                    └────────────────────────┬────────────────────────┘
                                             ▼  load_data.py (idempotent)
   ┌──────────────────────────── ONLINE ────────────────────────────┐
   Browser ─(Caddy :8080)─> Next.js web ─(/api proxy)─> FastAPI :8000
                                                            │
              answer_pipeline:  router ─> retrieval ─> composer ─> verifier
                                   │          │            │           │
                              intent    structured +   template /   trace-check
                                        hybrid RAG      Claude LLM   (rewrite ≤2)
                                                            ▼
                                         Postgres 16 + pgvector (claims/cells/chunks)
   └─────────────────────────────────────────────────────────────────┘
```

**Hai pha tách bạch:** engine tinh lọc (offline, domain-agnostic) vs app phục vụ (online). Ranh giới là `claims.jsonl` đã đóng băng + digest.

---

## 4. Backend — bản đồ 16 module (1.783 LOC)

| Module | LOC | Vai trò |
|---|---|---|
| `retrieval.py` | **502** | Tra cứu: structured (27 FIELD_RULES) + hybrid BM25/vector + fuzzy + nhân sự |
| `composer.py` | **270** | Dựng câu trả lời: template (fallback) & Claude; bảng điểm ấn phẩm; FIELD_LABELS |
| `main.py` | 185 | FastAPI app, 7 endpoint, rate-limit dependency, CORS |
| `verifier.py` | 118 | Trace-check: mọi số/tên phải neo được vào evidence; chống bịa |
| `telemetry.py` | 97 | Bộ đếm, null-backlog, /stats |
| `style_lint.py` | 82 | Lint văn phong (đếm phrase theo word-boundary) |
| `db.py` | 79 | Kết nối + schema (6 bảng) |
| `router.py` | 72 | Phân loại intent (oos/smalltalk/factual) |
| `pipeline.py` | 66 | Dây chuyền router→retrieval→composer→verifier, rewrite ≤2 |
| `constitution.py` | 66 | Hằng số miền: viết tắt, ngưỡng bảng (TABLE_MIN) |
| `models.py` | 60 | Contract Pydantic (Claim/Cell/Chunk/Citation/Answer) |
| `log.py` | 56 | JSON log có cấu trúc + request_id contextvar |
| `config.py` | 48 | Env: DATA_DIR, DATABASE_URL, LLM_ENABLED, EMBEDDINGS, MODE |
| `embeddings.py` | 44 | hash (offline) hoặc e5 (fastembed ONNX) |
| `ratelimit.py` | 38 | Cửa sổ trượt theo IP (10/phút, 100/giờ), trong tiến trình |

---

## 5. Data engine — kỷ luật bằng chứng (712 LOC)

`refinery.py` (434) + `bites.py` (278). **27 hàm cổng/điểm-cắn**, mỗi cổng fail-loud (raise → exit 2). Bộ răng (`bites.py`) là test âm: cố tình đưa dữ liệu bẩn, cổng PHẢI cắn.

**Cổng lõi (mọi domain):** `SOURCED_ATTR` · `CAPTURE_MISSING` · `SPAN_NOT_FOUND` · `AMBIGUOUS_MERGE_UNFLAGGED` · `DISTRIBUTION_NO_DENOMINATOR` · `IDEMPOTENT`.
**Cổng khai báo (domain-gates, bật theo config):** `ORIGIN_EVIDENCE` · `NO_INFERRED` · `STRATUM_MISMATCH` · `SCOPE_PLACEMENT` · `CAUSE_SOURCED` · `SEVERITY_SOURCED` · `NO_BLAME_INFERRED` · `REQUIRED_FIELD`.

**Bất biến then chốt:** `_norm(evidence_span) ⊂ _norm(snapshot)` — mỗi con số phải khớp byte (sau khi giải HTML-entity + NFC) với bản chụp gốc. Build **tất định** (idempotent), **auditor re-derive độc lập** với builder. Engine **domain-agnostic** — đã chứng minh qua đời registry 71→139 không đổi một dòng loader.

---

## 6. Retrieval — nhiều tầng (điểm kỹ thuật đậm nhất)

1. **Structured lookup** (`structured_lookup`, 27 FIELD_RULES) — deterministic, gánh chính. Year-filter (lọc field theo năm câu hỏi), default entity theo cấp (Trường vs chuyên-ngành).
2. **Nhân sự** — `_person_lookup` (tên riêng + kính ngữ), `_person_ambiguous` (tên trùng → hỏi lại), `_role_lookup` (tìm người theo chức vụ).
3. **Chịu lỗi đầu vào** — `_expand_abbrev` (viết tắt) + `_fuzzy_fix` (Levenshtein tự viết, ngưỡng 2) + anti-guess (viết tắt lạ chặn trước fuzzy).
4. **Hybrid RAG** — `hybrid_search`: BM25 (`rank-bm25`, cache khóa theo `_chunks_version()`) + pgvector, hợp nhất bằng **RRF**. Embedding: `hash` (char n-gram 384-chiều, tất định offline) hoặc `e5` (multilingual-e5-small qua fastembed ONNX).

**Triết lý:** KB nhỏ/đóng/cấu trúc-cao → structured lookup là trục chính, RAG hybrid là lưới đỡ. Không dùng GraphRAG/cross-encoder nặng.

---

## 7. Frontend — Next.js 15 App Router (943 LOC TS/TSX)

| Component | Vai trò |
|---|---|
| `ChatSurface.tsx` (126) | Khung hội thoại, orchestrate stream + AbortController |
| `EvidenceSheet.tsx` (106) | "Hồ sơ bằng chứng" slide-over: tier + URL sống + span (đã sanitize HTML) |
| `MessageBubble.tsx` (62) | Bong bóng hỏi/đáp, đề từ serif |
| `InputBar.tsx` (82) | Ô nhập v2: nút gửi ghost, nút dừng khi stream |
| `FeedbackBar` · `DisputedBlock` · `NullBlock` · `SeasonCards` · `TierBadge` · `CitationChip` | Khối chuyên biệt theo trạng thái |
| `ErrorBoundary.tsx` | Bọc lỗi runtime |
| `lib/cleanEvidence.ts` | Gỡ HTML thô khỏi span ở tầng hiển thị (dùng chung) |
| `middleware.ts` | Basic-auth gate staging |

Font: Fraunces (serif) + Be Vietnam Pro, next/font subset vietnamese. Thiết kế "UEL Edition" (#0090dc/#0b5c8d).

---

## 8. Cơ sở dữ liệu — 6 bảng (Postgres 16 + pgvector)

`claims` (claim đã đóng băng, claim_id = hash nội dung) · `registry_cells` (ô entity×field đã build, trạng thái sourced/corroborated/disputed/null) · `meta` (registry_version…) · `chunks` (corpus tầng 2 + vector) · `telemetry_events` (đếm + feedback) · `answer_cache` (khóa theo registry_version). Extension `vector` bắt buộc.

---

## 9. API contract & endpoint

**Contract (Pydantic):** `Capture`, `Claim`, `RegistryCell`, `Chunk`, `Citation`, `Answer`.
**Endpoint:** `GET /health` · `POST /chat` · `POST /chat/stream` · `POST /telemetry` · `GET /telemetry/nulls` · `GET /telemetry/stats` · `GET /admin` (auth riêng).

**Luồng trả lời** (`answer_pipeline`): `router` phân intent → `retrieve` → `compose` (template hoặc Claude) → `verify` trace-check → nếu vi phạm & `LLM_ENABLED`: rewrite tối đa **2 vòng** → quá thì SAFE_FALLBACK + log. Cache theo `registry_version`.

---

## 10. Chất lượng & kiểm thử

| Bộ đo | Kết quả |
|---|---|
| pytest | **58 hàm / 9 file** (ingest, retrieval, person v19, bm25 cache, style-lint, pipeline, ratelimit, verifier, typo v14) |
| Golden set | 55 câu · status_accuracy **0.945** · recall/cov 0.955 · gate `--compare` delta≥0 |
| Smoke | 12/12 qua HTTP + rate-limit thật · P95 0.07s |
| Engine | bites: mọi răng cắn ✓ · build idempotent · auditor OK |

---

## 11. DevOps & triển khai

- **Docker Compose 4 service**: db (pgvector) · api (FastAPI) · web (Next.js) · caddy. `entrypoint.sh` chạy loader idempotent lúc start.
- Cổng: Caddy 8080 · api 8000 · web 3002 · db `DB_HOST_PORT` (5453 trên máy này; 5433 mặc định).
- **Staging hardening**: basic-auth + noindex + robots.txt + `/admin` telemetry; CORS deny mặc định; rate-limit đọc `X-Forwarded-For` sau Caddy.
- `render.yaml` blueprint sẵn (chưa provision).
- Repo private `github.com/nclamvn/chatbotUEL`.

---

## 12. Điểm mạnh kỹ thuật & nợ kỹ thuật (trung thực)

**Mạnh:**
- Kỷ luật bằng chứng cưỡng chế bằng code (27 cổng), không phải quy ước — sai một byte thì build dừng.
- Tách pha offline/online sạch; engine domain-agnostic tái dùng được (đã chứng minh).
- Deterministic-first: hash embedding + structured lookup → chạy offline, test tất định, không phụ thuộc mạng.
- Codebase nhỏ (<3.5K LOC logic), dễ audit toàn bộ.

**Nợ / giới hạn:**
- Đang `MODE=template` — composer LLM (Claude) chưa bật (chờ key); con số golden đo trên đường fallback.
- Một số dữ liệu chỉ reachable qua LLM (đọc chunk dài).
- 22/139 evidence_span là HTML thô (verbatim đúng) — đã vá tầng hiển thị; **fix gốc** (span sạch / field `evidence_display`) thuộc refinery, để dành khi phá băng.
- Rate-limit giữ trong tiến trình (chưa phân tán) — đủ cho pilot, cần Redis khi scale.
- 1 tác giả, 17 commit — dự án trẻ, chưa CI tự động (test chạy tay/entrypoint).

---
*X-ray sinh từ trạng thái thực HEAD `b7ea693` · đo sống LOC & version 21/07/2026.*
