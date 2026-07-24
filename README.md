# Chatbot UEL · Khoa Toán Kinh tế

Repository bàn giao cổng hỏi đáp tuyển sinh của Khoa Toán Kinh tế,
Trường Đại học Kinh tế - Luật, ĐHQG-HCM.

Ứng dụng trả lời dựa trên **139 dữ kiện đã kiểm chứng** trong Registry v1.3.
Mỗi số liệu và tên riêng đều truy vết được về nguồn; hệ thống hỗ trợ bốn trạng
thái: grounded, disputed, honest-null và ngoài phạm vi.

## Khởi chạy nhanh

```bash
cd tkt-bot
cp .env.example .env
docker compose up -d --build
```

Mở [http://localhost:8080](http://localhost:8080).

Mặc định ứng dụng chạy chế độ **Demo** ổn định và không gọi API bên ngoài.
Chỉ toggle **AI trực tiếp** mới sử dụng OpenAI, với Claude làm fallback khi phía
Trường đã cấu hình key hợp lệ và đặt `MODE=llm`.

## Cấu trúc chính

| Thư mục | Nội dung |
|---|---|
| [`tkt-bot/`](./tkt-bot/) | FastAPI, Next.js, PostgreSQL/pgvector và Docker Compose |
| [`toan_kinh_te_uel/`](./toan_kinh_te_uel/) | Registry, claims và snapshot nguồn |
| [`tkt-bot/README.md`](./tkt-bot/README.md) | Hướng dẫn vận hành và bàn giao đầy đủ |

## Bảo mật khi bàn giao

- Repository không chứa API key cá nhân.
- Không commit file `.env`.
- Phía Trường tạo key riêng, lưu trong secret manager của nền tảng triển khai,
  đặt hạn mức chi tiêu và bật cảnh báo usage.
- Khi chưa có key thuộc quyền quản lý của Trường, giữ `MODE=template`.

Chi tiết cấu hình provider, kiểm tra health, smoke test và unit test nằm trong
[`tkt-bot/README.md`](./tkt-bot/README.md).
