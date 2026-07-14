const state = { sessionId: null, es: null, chart: null, defaults: null };

const $ = (id) => document.getElementById(id);

function on(id, event, handler) {
  const el = $(id);
  if (!el) {
    console.warn(`[ReqValLive] elemento #${id} não encontrado — skip ${event}`);
    return;
  }
  el.addEventListener(event, handler);
}

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
  const panel = $(`panel-${n}`);
  const btn = document.querySelector(`.step[data-step="${n}"]`);
  if (panel) panel.classList.add("active");
  if (btn) {
    btn.classList.add("active");
    btn.disabled = false;
  }
}

async function loadDefaults() {
  try {
    const res = await fetch("/api/defaults");
    state.defaults = await res.json();
    if ($("mqtt-broker")) $("mqtt-broker").value = state.defaults.mqtt_broker;
    if ($("mqtt-port")) $("mqtt-port").value = state.defaults.mqtt_port;
    if ($("mqtt-topic")) $("mqtt-topic").value = state.defaults.mqtt_topic;
    if ($("mqtt-user")) $("mqtt-user").value = state.defaults.mqtt_username || "";
    const hint = [];
    if (!state.defaults.llm_configured) {
      hint.push("LLM_API_KEY não configurada no .env.");
    }
    hint.push(`LLM: ${state.defaults.llm_model} @ ${state.defaults.llm_base_url}`);
    if ($("out-1")) $("out-1").textContent = hint.join(" ");
  } catch (e) {
    if ($("out-1")) $("out-1").textContent = `Falha ao carregar defaults: ${e}`;
  }
}

function mqttBody() {
  return {
    mqtt_broker: $("mqtt-broker")?.value || state.defaults?.mqtt_broker,
    mqtt_port: Number($("mqtt-port")?.value || state.defaults?.mqtt_port || 1883),
    mqtt_topic: $("mqtt-topic")?.value || state.defaults?.mqtt_topic,
    mqtt_username: $("mqtt-user")?.value || "",
    mqtt_password: $("mqtt-pass")?.value || "",
  };
}

function renderSession(session) {
  state.sessionId = session.id;
  if (window.ReqValDiagram) {
    window.ReqValDiagram.render($("sysml-canvas"), session);
    window.ReqValDiagram.render($("sysml-live"), session);
  }
  if ($("sysml-preview")) $("sysml-preview").textContent = session.sysml_preview || "";
  if ($("btn-dl-sysml")) $("btn-dl-sysml").href = `/api/sessions/${session.id}/sysml`;
  if ($("btn-dl-md")) $("btn-dl-md").href = `/api/sessions/${session.id}/model.md`;
  if ($("btn-report")) $("btn-report").href = `/api/sessions/${session.id}/report`;
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
  if ($("mqtt-status-pill")) $("mqtt-status-pill").textContent = statusLabel(session.mqtt_status);
  if ($("conn-pill")) {
    $("conn-pill").textContent = session.connected ? "conectado" : statusLabel(session.mqtt_status);
  }
  if ($("btn-start-monitor")) {
    $("btn-start-monitor").disabled = !session.connected && session.mqtt_status === "disconnected";
  }

  const stats = $("drone-stats");
  if (stats) {
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
  }

  const feed = $("msg-feed");
  if (feed) {
    feed.innerHTML = (session.message_log || [])
      .slice()
      .reverse()
      .map((m) => {
        const t = new Date(m.ts * 1000).toLocaleTimeString();
        return `<div>[${t}] ${m.drone} bat=${m.batteryLevel ?? "—"} lat=${m.lat ?? "—"} lon=${m.lon ?? "—"}</div>`;
      })
      .join("");
  }

  if ($("out-4")) $("out-4").textContent = JSON.stringify(session.summary || {}, null, 2);
  if (window.ReqValDiagram) window.ReqValDiagram.render($("sysml-live"), session);
  updateChart(session);
}

function updateChart(session) {
  const canvas = $("live-chart");
  if (!canvas || typeof Chart === "undefined") return;
  const drones = session.drones || [];
  const labels = drones.map((d) => d.id);
  const values = drones.map((d) => d.battery ?? null);
  if (!state.chart) {
    state.chart = new Chart(canvas, {
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
  if ($("out-1")) $("out-1").textContent = "Chamando LLM…";
  const res = await fetch("/api/requirements/from-markdown", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ markdown: $("md-input").value, ...mqttBody() }),
  });
  const data = await res.json();
  if (!res.ok) {
    if ($("out-1")) $("out-1").textContent = JSON.stringify(data, null, 2);
    return;
  }
  if ($("out-1")) {
    $("out-1").textContent = `OK — ${data.requirements?.length || 0} requisito(s). ${data.llm_notes || ""}`;
  }
  renderSession(data);
  gotoStep(2);
  document.querySelector('.step[data-step="3"]').disabled = false;
  document.querySelector('.step[data-step="4"]').disabled = false;
}

async function applyMqttAndConnect() {
  if (!state.sessionId) {
    if ($("out-3")) $("out-3").textContent = "Gere o modelo (passo 1) antes de conectar.";
    return;
  }
  await fetch(`/api/sessions/${state.sessionId}/mqtt`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(mqttBody()),
  });
  const res = await fetch(`/api/sessions/${state.sessionId}/connect`, { method: "POST" });
  const data = await res.json();
  if ($("out-3")) {
    $("out-3").textContent = JSON.stringify(
      { mqtt_status: data.mqtt_status, connected: data.connected, error: data.last_error },
      null,
      2
    );
  }
  updateMonitor(data);
  startStream();
  if ($("btn-start-monitor")) $("btn-start-monitor").disabled = false;
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

async function probeLlm() {
  if ($("out-1")) $("out-1").textContent = "Testando LLM…";
  try {
    const res = await fetch("/api/llm/probe");
    const data = await res.json();
    if ($("out-1")) $("out-1").textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    if ($("out-1")) $("out-1").textContent = String(e);
  }
}

function bindUi() {
  document.querySelectorAll(".step").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (!btn.disabled) gotoStep(Number(btn.dataset.step));
    });
  });

  on("btn-load-sample-md", "click", () => {
    if ($("md-input")) $("md-input").value = SAMPLE_MD;
  });
  on("md-file", "change", async (ev) => {
    const file = ev.target.files?.[0];
    if (!file || !$("md-input")) return;
    $("md-input").value = await file.text();
  });
  on("btn-interpret", "click", () => interpretMd().catch((e) => {
    if ($("out-1")) $("out-1").textContent = String(e);
  }));
  on("btn-probe-llm", "click", () => probeLlm());
  on("btn-goto-mqtt", "click", () => gotoStep(3));
  on("btn-connect", "click", () => applyMqttAndConnect().catch(console.error));
  on("btn-disconnect", "click", async () => {
    if (!state.sessionId) return;
    const res = await fetch(`/api/sessions/${state.sessionId}/disconnect`, { method: "POST" });
    updateMonitor(await res.json());
  });
  on("btn-start-monitor", "click", () => startMonitor().catch(console.error));
  on("btn-stop-monitor", "click", () => stopMonitor().catch(console.error));

  if ($("md-input") && !$("md-input").value.trim()) {
    $("md-input").value = SAMPLE_MD;
  }
  loadDefaults();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bindUi);
} else {
  bindUi();
}
