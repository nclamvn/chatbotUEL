// Vài claim (điểm chuẩn ts247/hocmai, một số CV) có evidence_span là nguyên khối
// HTML vì nguồn render bằng <table>/<strong>; gate verbatim giữ markup là chuỗi gốc
// duy nhất trong snapshot. Ở tầng HIỂN THỊ chỉ gỡ thẻ để đọc được (ô bảng nối bằng
// " · "), KHÔNG đổi claim đã lưu — bản audit vẫn byte-exact. Fix gốc (span sạch hoặc
// field evidence_display) thuộc refinery. Dùng chung cho EvidenceSheet + DisputedBlock.
export function cleanEvidence(raw: string): string {
  if (!raw || !/<[a-z/]/i.test(raw)) return raw; // không phải HTML thì giữ nguyên
  return raw
    .replace(/<\/(td|th|tr|p|div|li)>/gi, " · ")
    .replace(/<[^>]+>/g, "")
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/\s+/g, " ")
    .replace(/(\s*·\s*)+/g, " · ")
    .replace(/^[·\s]+|[·\s]+$/g, "")
    .trim();
}
