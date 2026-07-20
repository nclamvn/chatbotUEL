import React from "react";

function inline(text: string, keyBase: string): React.ReactNode[] {
  // chỉ hỗ trợ **đậm**, phần còn lại là chữ thường đã được React escape
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((p, i) =>
    p.startsWith("**") && p.endsWith("**") ? (
      <b key={`${keyBase}-${i}`}>{p.slice(2, -2)}</b>
    ) : (
      p
    ),
  );
}

export function renderMarkdown(text: string): React.ReactNode[] {
  const blocks = text.split(/\n\s*\n/).filter((b) => b.trim());
  return blocks.map((block, bi) => {
    const lines = block.split("\n").filter((l) => l.trim());

    // bảng markdown: | header |, | --- |, rồi các dòng dữ liệu
    const isTable =
      lines.length >= 2 &&
      lines.every((l) => l.trim().startsWith("|")) &&
      lines[1].includes("---");
    if (isTable) {
      const cells = (l: string) =>
        l.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
      const header = cells(lines[0]);
      const body = lines.slice(2).map(cells);
      return (
        <table key={bi}>
          <thead>
            <tr>
              {header.map((c, i) => (
                <th key={i}>{inline(c, `${bi}-th-${i}`)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {body.map((row, ri) => (
              <tr key={ri}>
                {row.map((c, ci) => (
                  <td key={ci}>{inline(c, `${bi}-td-${ri}-${ci}`)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      );
    }

    const isList = lines.every((l) => l.trim().startsWith("- "));
    if (isList) {
      return (
        <ul key={bi}>
          {lines.map((l, li) => (
            <li key={li}>{inline(l.trim().slice(2), `${bi}-${li}`)}</li>
          ))}
        </ul>
      );
    }
    const mixed: React.ReactNode[] = [];
    let listBuf: string[] = [];
    let k = 0;
    const flush = () => {
      if (!listBuf.length) return;
      mixed.push(
        <ul key={`ul-${k++}`}>
          {listBuf.map((l, li) => (
            <li key={li}>{inline(l, `${bi}-ul-${li}`)}</li>
          ))}
        </ul>,
      );
      listBuf = [];
    };
    for (const line of lines) {
      if (line.trim().startsWith("- ")) {
        listBuf.push(line.trim().slice(2));
      } else {
        flush();
        mixed.push(<p key={`p-${k++}`}>{inline(line, `${bi}-p-${k}`)}</p>);
      }
    }
    flush();
    return <div key={bi}>{mixed}</div>;
  });
}
