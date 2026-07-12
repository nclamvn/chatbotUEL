# Domain: toan_kinh_te_uel

Quy trình 6 bước (xem refinery/README.md cho chi tiết):

1. Sửa `domain.yaml`: schema.fields, type_field, rollup_field, universe.estimate (mẫu số).
2. Cào nguồn, lưu mỗi trang vào `snapshots/<ten>.html` (bản chụp raw).
3. Đổ claim đã trích vào `claims.jsonl`, mỗi value kèm `evidence_span` verbatim + `capture.snapshot`.
4. `python refinery.py domains/toan_kinh_te_uel`        # build + present
5. `python bites.py domains/toan_kinh_te_uel`           # chứng minh mọi cổng cắn
6. Honest-null "—" cho field trống, disputed giữ trọn, phân bố kèm mẫu số.

Một dòng claims.jsonl mẫu nằm sẵn trong file (xoá khi bắt đầu thật).
