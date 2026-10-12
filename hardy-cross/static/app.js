const $ = (sel) => document.querySelector(sel);

function pipeRow(p = {}) {
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td><input value="${p.id ?? ""}" data-k="id"></td>
    <td><input value="${p.start ?? ""}" data-k="start"></td>
    <td><input value="${p.end ?? ""}" data-k="end"></td>
    <td><input type="number" step="any" value="${p.length_m ?? ""}" data-k="length_m"></td>
    <td><input type="number" step="any" value="${p.diameter_m ?? ""}" data-k="diameter_m"></td>
    <td><input type="number" step="any" value="${p.k ?? ""}" data-k="k" placeholder="자동"></td>
    <td><input type="number" step="any" value="${p.c ?? 100}" data-k="c"></td>
    <td><input type="number" step="any" value="${p.q_m3s ?? ""}" data-k="q_m3s"></td>
    <td><button type="button" class="ghost tiny">×</button></td>`;
  tr.querySelector("button").onclick = () => tr.remove();
  return tr;
}

function loopRow(lp = {}) {
  const tr = document.createElement("tr");
  const members = (lp.members || [])
    .map((m) => (m.sign < 0 ? `-${m.pipe}` : m.pipe))
    .join(", ");
  tr.innerHTML = `
    <td><input value="${lp.id ?? ""}" data-k="id"></td>
    <td><input value="${members}" data-k="members" placeholder="1, -2, -3"></td>
    <td><button type="button" class="ghost tiny">×</button></td>`;
  tr.querySelector("button").onclick = () => tr.remove();
  return tr;
}

function readPipes() {
  return [...$("#pipes tbody").rows].map((row) => {
    const g = (k) => row.querySelector(`[data-k="${k}"]`).value;
    return {
      id: g("id").trim(),
      start: g("start").trim(),
      end: g("end").trim(),
      length_m: Number(g("length_m")),
      diameter_m: Number(g("diameter_m")),
      c: Number(g("c")),
      k: g("k") === "" ? null : Number(g("k")),
      q_m3s: Number(g("q_m3s")),
    };
  });
}

function parseMembers(text) {
  return text
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean)
    .map((tok) => {
      if (tok.startsWith("-")) return { pipe: tok.slice(1).trim(), sign: -1 };
      if (tok.startsWith("+")) return { pipe: tok.slice(1).trim(), sign: 1 };
      return { pipe: tok, sign: 1 };
    });
}

function readLoops() {
  return [...$("#loops tbody").rows].map((row) => ({
    id: row.querySelector('[data-k="id"]').value.trim(),
    members: parseMembers(row.querySelector('[data-k="members"]').value),
  }));
}

function payload() {
  return {
    formula: $("#formula").value,
    tolerance: Number($("#tol").value),
    max_iter: Number($("#maxiter").value),
    nodes: window.__nodes || [],
    pipes: readPipes(),
    loops: readLoops(),
  };
}

function fillNetwork(data) {
  window.__nodes = data.nodes || [];
  $("#formula").value = data.formula || "hazen_williams";
  if (data.tolerance) $("#tol").value = data.tolerance;
  if (data.max_iter) $("#maxiter").value = data.max_iter;
  const pb = $("#pipes tbody");
  pb.innerHTML = "";
  (data.pipes || []).forEach((p) => pb.appendChild(pipeRow(p)));
  const lb = $("#loops tbody");
  lb.innerHTML = "";
  (data.loops || []).forEach((lp) => lb.appendChild(loopRow(lp)));
}

function fmt(x, n = 5) {
  if (x == null || Number.isNaN(x)) return "—";
  return Number(x).toExponential ? Number(x).toFixed(n) : x;
}

function drawNetwork(nodes, pipes) {
  const svg = $("#net");
  svg.innerHTML = "";
  if (!nodes.length) {
    svg.innerHTML = `<text x="16" y="28" fill="#8b9bb0">절점 좌표가 있는 예제를 불러오면 도식이 그려집니다.</text>`;
    return;
  }
  const map = Object.fromEntries(nodes.map((n) => [n.id, n]));
  const flowMap = Object.fromEntries((pipes || []).map((p) => [p.id, p]));
  const inputPipes = readPipes();

  for (const p of inputPipes) {
    const a = map[p.start];
    const b = map[p.end];
    if (!a || !b) continue;
    const res = flowMap[p.id];
    const q = res ? res.q_m3s : p.q_m3s;
    const reverse = q < 0;
    const x1 = reverse ? b.x : a.x;
    const y1 = reverse ? b.y : a.y;
    const x2 = reverse ? a.x : b.x;
    const y2 = reverse ? a.y : b.y;
    const mag = Math.min(8, 2 + Math.abs(q) * 1.2);
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", x1);
    line.setAttribute("y1", y1);
    line.setAttribute("x2", x2);
    line.setAttribute("y2", y2);
    line.setAttribute("stroke", "#3d9cf0");
    line.setAttribute("stroke-width", String(mag));
    line.setAttribute("marker-end", "url(#arrow)");
    svg.appendChild(line);
    const mx = (a.x + b.x) / 2;
    const my = (a.y + b.y) / 2;
    const t = document.createElementNS("http://www.w3.org/2000/svg", "text");
    t.setAttribute("x", mx + 6);
    t.setAttribute("y", my - 6);
    t.setAttribute("fill", "#e8eef6");
    t.setAttribute("font-size", "12");
    t.textContent = `${p.id}  ${fmt(q, 4)} m³/s`;
    svg.appendChild(t);
  }

  const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
  defs.innerHTML = `<marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
    <path d="M0,0 L8,4 L0,8 z" fill="#3d9cf0"/></marker>`;
  svg.insertBefore(defs, svg.firstChild);

  for (const n of nodes) {
    const c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    c.setAttribute("cx", n.x);
    c.setAttribute("cy", n.y);
    c.setAttribute("r", 10);
    c.setAttribute("fill", "#171e27");
    c.setAttribute("stroke", "#3ecf8e");
    c.setAttribute("stroke-width", "2");
    svg.appendChild(c);
    const t = document.createElementNS("http://www.w3.org/2000/svg", "text");
    t.setAttribute("x", n.x + 14);
    t.setAttribute("y", n.y + 4);
    t.setAttribute("fill", "#3ecf8e");
    t.setAttribute("font-size", "13");
    t.textContent = n.label || n.id;
    svg.appendChild(t);
  }
}

function showResult(data) {
  const msg = $("#msg");
  msg.textContent = data.message;
  msg.className = "msg " + (data.converged ? "ok" : "bad");

  const tb = $("#out tbody");
  tb.innerHTML = "";
  for (const p of data.pipes) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${p.id}</td><td>${p.start}→${p.end}</td>
      <td>${fmt(p.q_m3s, 6)}</td><td>${fmt(p.velocity_ms, 4)}</td>
      <td>${fmt(p.head_loss_m, 5)}</td><td>${fmt(p.r, 3)}</td>`;
    tb.appendChild(tr);
  }

  const hist = (data.history || [])
    .map(
      (h) =>
        `${String(h.iteration).padStart(3)}  max|ΔQ|=${h.max_abs_dq.toExponential(3)}  max|Σhf|=${h.max_abs_sum_hf.toExponential(3)}  ` +
        h.loops.map((l) => `${l.loop_id}:ΔQ=${l.delta_q.toExponential(2)}`).join("  ")
    )
    .join("\n");
  $("#hist").textContent = hist || "(없음)";
  drawNetwork(data.nodes || window.__nodes || [], data.pipes);
}

$("#add-pipe").onclick = () => $("#pipes tbody").appendChild(pipeRow());
$("#add-loop").onclick = () => $("#loops tbody").appendChild(loopRow());

$("#load").onclick = async () => {
  const res = await fetch("/api/example");
  const data = await res.json();
  fillNetwork(data);
  drawNetwork(data.nodes, data.pipes);
  $("#msg").textContent = "예제 5.14(표 5.5.1)를 불러왔습니다. 해석을 누르세요.";
  $("#msg").className = "msg";
};

$("#solve").onclick = async () => {
  const res = await fetch("/api/solve", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload()),
  });
  const data = await res.json();
  if (!res.ok) {
    $("#msg").textContent = data.error || "해석 실패";
    $("#msg").className = "msg bad";
    return;
  }
  showResult(data);
};

window.addEventListener("DOMContentLoaded", () => {
  $("#load").click();
});
