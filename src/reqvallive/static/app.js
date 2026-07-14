const state = { sessionId: null, es: null, chart: null, defaults: null };

const $ = (id) => document.getElementById(id);

const SAMPLE_MD = `# Requisitos de missão UTM

## RQ-BAT-001 — Bateria mínima
O sistema deve manter o nível de bateria de **cada drone** acima de **20%** durante toda a operação.
Critério: batteryLevel >= 20 (percent), scope all entities.

## RQ-SEP-001 — Separação mínima
O sistema deve manter separação mínima de **20 metros** entre quaisquer dois drones em voo simultâneo.
Critério: min_separation_m >= 20 (meters).
`;

function gotoStep(n) {
  document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
  document.querySelectorAll(".step").forEach((b) => b.classList.remove("active"));
  $(`panel-${n}`).classList.add("active");
  const btn = document.querySelector(`.step[data-step="${n}"]`);
  btn.classList.add("active");
  btn.disabled = false;
}

async function loadDefaults() {
  const res = await fetch("/api/defaults");
  state.defaults = await res.json();
  $("mqtt-broker").value = state.defaults.mqtt_broker;
  $("mqtt-port").value = state.defaults.mqtt_port;
  $("mqtt-topic").value = state.defaults.mqtt_topic;
  $("mqtt-user").value = state.defaults.mqtt_username || "";
  if (!state.defaults.llm_configured) {
    $("out-1").textContent =
      "Aviso: LLM_API_KEY não configurada no .env — configure antes de interpretar Markdown.";
  }
}

function mqttBody() {
  return {
    mqtt_broker: $("mqtt-broker").value || state.defaults?.mqtt_broker,
    mqtt_port: Number($("mqtt-port").value || state.defaults?.mqtt_port || 1883),
    mqtt_topic: $("mqtt-topic").value || state.defaults?.mqtt_topic,
    mqtt_username: $("mqtt-user").value || "",
    mqtt_password: $("mqtt-pass").value || "",
  };
}

function renderSession(session) {
  state.sessionId = session.id;
  window.ReqValDiagram.render($("sysml-canvas"), session);
  window.ReqValDiagram.render($("sysml-live"), session);
  $("sysml-preview").textContent = session.sysml_preview || "";
  $("btn-dl-sysml").href = `/api/sessions/${session.id}/sysml`;
  $("btn-dl-md").href = `/api/sessions/${session.id}/model.md`;
  $("btn-report").href = `/api/sessions/${session.id}/report`;
  updateMonitor(session);
}

function statusLabel(s) {
  const map = {
    disconnected: "desconectado",
    connecting: "conectando…",
    listening: "escutando",
    no_messages: "sem mensagens",
    error: "falha de conexão",
  };
  return map[s] || s || "—";
}

function updateMonitor(session) {
  $("mqtt-status-pill").textContent = statusLabel(session.mqtt_status);
  $("conn-pill").textContent = session.connected ? "conectado" : statusLabel(session.mqtt_status);
  $("btn-start-monitor").disabled = !session.connected && session.mqtt_status === "disconnected";

  const stats = $("drone-stats");
  stats.innerHTML = (session.drones || [])
    .map((d) => {
      const oks = Object.entries(d.ok_by_req || {})
        .map(([k, v]) => `${k}:${v === true ? "OK" : v === false ? "NOK" : "—"}`)
        .join(" · ");
      return `<div class="drone-card"><strong>${d.id}</strong>
        bat=${d.battery ?? "—"} · pos=${d.latitude != null ? d.latitude.toFixed(5) : "—"},${d.longitude != null ? d.longitude.toFixed(5) : "—"}
        <div class="muted">${oks || "aguardando avaliação"}</div></div>`;
    })
    .join("") || '<div class="muted">Nenhum drone ainda</div>';

  const feed = $("msg-feed");
  feed.innerHTML = (session.message_log || [])
    .slice()
    .reverse()
    .map((m) => {
      const t = new Date(m.ts * 1000).toLocaleTimeString();
      return `<div>[${t}] ${m.drone} bat=${m.batteryLevel ?? "—"} lat=${m.lat ?? "—"} lon=${m.lon ?? "—"}</div>`;
    })
    .join("");

  $("out-4").textContent = JSON.stringify(session.summary || {}, null, 2);
  window.ReqValDiagram.render($("sysml-live"), session);
  updateChart(session);
}

function updateChart(session) {
  const drones = session.drones || [];
  const labels = drones.map((d) => d.id);
  const values = drones.map((d) => d.battery ?? null);
  if (!state.chart) {
    state.chart = new Chart($("live-chart"), {
      type: "bar",
      data: { labels, datasets: [{ label: "batteryLevel", data: values, backgroundColor: "#1e3a5f" }] },
      options: { animation: false, plugins: { legend: { display: false } }, scales: { y: { min: 0, max: 100 } } },
    });
  } else {
    state.chart.data.labels = labels;
    state.chart.data.datasets[0].data = values;
    state.chart.update("none");
  }
}

function startStream() {
  if (state.es) state.es.close();
  if (!state.sessionId) return;
  state.es = new EventSource(`/api/sessions/${state.sessionId}/stream`);
  state.es.onmessage = (ev) => {
    const session = JSON.parse(ev.data);
    updateMonitor(session);
  };
}

async function interpretMd() {
  $("out-1").textContent = "Chamando LLM…";
  const res = await fetch("/api/requirements/from-markdown", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ markdown: $("md-input").value, ...mqttBody() }),
  });
  const data = await res.json();
  if (!res.ok) {
    $("out-1").textContent = JSON.stringify(data, null, 2);
    return;
  }
  $("out-1").textContent = `OK — ${data.requirements?.length || 0} requisito(s). ${data.llm_notes || ""}`;
  renderSession(data);
  gotoStep(2);
  document.querySelector('.step[data-step="3"]').disabled = false;
  document.querySelector('.step[data-step="4"]').disabled = false;
}

async function applyMqttAndConnect() {
  await fetch(`/api/sessions/${state.sessionId}/mqtt`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(mqttBody()),
  });
  const res = await fetch(`/api/sessions/${state.sessionId}/connect`, { method: "POST" });
  const data = await res.json();
  $("out-3").textContent = JSON.stringify(
    { mqtt_status: data.mqtt_status, connected: data.connected, error: data.last_error },
    null,
    2
  );
  updateMonitor(data);
  startStream();
  $("btn-start-monitor").disabled = false;
}

async function startMonitor() {
  const res = await fetch(`/api/sessions/${state.sessionId}/start`, { method: "POST" });
  const data = await res.json();
  updateMonitor(data);
  startStream();
  gotoStep(4);
}

async function stopMonitor() {
  const res = await fetch(`/api/sessions/${state.sessionId}/stop`, { method: "POST" });
  const data = await res.json();
  updateMonitor(data);
}

document.querySelectorAll(".step").forEach((btn) => {
  btn.addEventListener("click", () => {
    if (!btn.disabled) gotoStep(Number(btn.dataset.step));
  });
});

$("btn-load-sample-md").addEventListener("click", () => {
  $("md-input").value = SAMPLE_MD;
});
$("md-file").addEventListener("change", async (ev) => {
  const file = ev.target.files?.[0];
  if (!file) return;
  $("md-input").value = await file.text();
});
$("btn-interpret").addEventListener("click", () => interpretMd().catch((e) => ($("out-1").textContent = String(e))));
$("btn-goto-mqtt").addEventListener("click", () => gotoStep(3));
$("btn-connect").addEventListener("click", () => applyMqttAndConnect().catch(console.error));
$("btn-disconnect").addEventListener("click", async () => {
  const res = await fetch(`/api/sessions/${state.sessionId}/disconnect`, { method: "POST" });
  updateMonitor(await res.json());
});
$("btn-start-monitor").addEventListener("click", () => startMonitor().catch(console.error));
$("btn-stop-monitor").addEventListener("click", () => stopMonitor().catch(console.error));

$("md-input").value = SAMPLE_MD;
loadDefaults();
