import type { Answer } from "./types";

// Đường dẫn tương đối: dev đi qua rewrites của Next, production đi qua Caddy.
// Bài học hạ tầng: không hardcode URL tuyệt đối trong standalone build.
const API_BASE = "/api";

export interface StreamHandlers {
  onPartial: (text: string) => void;
  onAnswer: (answer: Answer) => void;
  onError: (err: string) => void;
}

export async function streamChat(message: string, h: StreamHandlers): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
  } catch {
    h.onError("Không kết nối được máy chủ. Bạn thử lại sau nhé.");
    return;
  }
  if (!res.ok || !res.body) {
    h.onError("Máy chủ đang bận. Bạn thử lại sau nhé.");
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const events = buf.split("\n\n");
    buf = events.pop() ?? "";
    for (const evt of events) {
      const lines = evt.split("\n");
      const type = lines.find((l) => l.startsWith("event: "))?.slice(7);
      const data = lines.find((l) => l.startsWith("data: "))?.slice(6);
      if (!type || !data) continue;
      if (type === "partial") h.onPartial(JSON.parse(data).text);
      if (type === "answer") h.onAnswer(JSON.parse(data) as Answer);
    }
  }
}
