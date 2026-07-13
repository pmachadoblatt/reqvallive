const state = {
  sessionId: null,
  exampleJson: null,
  es: null,
  chart: null,
};

const $ = (id) => document.getElementById(id);

async function loadExample() {
  const res = await fetch("/static/battery_threshold.json").catch(() => null);
  if (res && res.ok) {
    state.exampleJson = await res.json();
  } else {
    // fallback embutido se static copy falhar
    state.exampleJson = {
      req_id: "RQ-BAT-001",
      title: "Nível mínimo de bateria durante a missão",
      text: "O sistema deve manter o nível de bateria da aeronave acima de 20% durante toda a operação",
      rationale: "Evitar RTL forçado e perda de telemetria por descarga crítica.",
      level: "system",
      conops_ref: "CONOPS-UTM §4.2",
      source: "ReqValLive MVP",
      priority: "high",
      vv_method: "test",
      success_criteria: {
        type: "threshold",
        metric: "battery_level",
        operator: ">=",
        value: 20.0,
        unit: "percent",
        scope: "all_timesteps",
        tolerance: 0.0,
      },
      tags: ["battery", "safety", "mqtt"],
    };
  }
  $("req-json").value = JSON.stringify(state.exampleJson, null, 2);
}

function gotoStep(n) {
  document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
  document.querySelectorAll(".step").forEach((b) => b.classList.remove("active"));
  $(`panel-${n}`).classList.add("active");
  const btn = document.querySelector(`.step[data-step="${n}"]`);
  btn.classList.add("active");
  btn.disabled = false;
}

function parseRequirementJson() {
  const raw = JSON.parse($("req-json").value);
  if (raw.requirements && Array.isArray(raw.requirements)) {
    return { requirement: raw.requirements[0] };
  }
  return { requirement: raw };
}

async function validateRequirement() {
  const body = parseRequirementJson();
  const res = await fetch("/api/requirements/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  $("validate-out").textContent = JSON.stringify(data, null, 2);
  $("btn-create-session").disabled = !res.ok;
  if (!res.ok) throw new Error(data.detail?.message || "Validação falhou");
  return data;
}

function mqttBody() {
  return {
    mqtt_broker: $("mqtt-broker").value || "127.0.0.1",
    mqtt_port: Number($("mqtt-port").value || 1883),
    mqtt_topic: $("mqtt-topic").value || "conceptio/reqval",
    mqtt_username: $("mqtt-user").value || "",
    mqtt_password: $("mqtt-pass").value || "",
  };
}

function renderSession(session) {
  state.sessionId = session.id;
  $("d-req-id").textContent = session.req_id;
  $("d-req-title").textContent = session.title;
  $("d-metric").textContent = session.metric;
  $("d-constraint").textContent = JSON.stringify(session.success_criteria);
  $("sysml-preview").textContent = session.sysml_preview || "";
  $("btn-export-sysml").href = `/api/sessions/${session.id}/sysml`;
  $("btn-report").href = `/api/sessions/${session.id}/report`;
  updateLive(session);
  gotoStep(2);
  document.querySelector('.step[data-step="3"]').disabled = false;
  document.querySelector('.step[data-step="4"]').disabled = false;
}

async function createSession() {
  const body = { ...parseRequirementJson(), ...mqttBody() };
  const res = await fetch("/api/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) {
    $("validate-out").textContent = JSON.stringify(data, null, 2);
    throw new Error("Falha ao criar sessão");
  }
  renderSession(data);
}

function updateLive(session) {
  $("live-value").textContent = session.last_value ?? "—";
  $("live-count").textContent = session.summary?.sample_count ?? 0;
  $("live-violations").textContent = session.summary?.violations ?? 0;
  $("d-value").textContent = session.last_value ?? "—";
  const badge = $("live-ok");
  const dBadge = $("d-badge");
  if (session.last_ok === true) {
    badge.textContent = "OK";
    badge.className = "badge ok";
    dBadge.textContent = "OK";
    dBadge.className = "badge ok";
  } else if (session.last_ok === false) {
    badge.textContent = "NOK";
    badge.className = "badge nok";
    dBadge.textContent = "NOK";
    dBadge.className = "badge nok";
  } else {
    badge.textContent = "—";
    badge.className = "badge";
    dBadge.textContent = "—";
    dBadge.className = "badge";
  }
  $("mqtt-status").textContent = session.measuring
    ? session.mqtt_connected
      ? "ligado"
      : "conectando…"
    : "parado";
  $("live-error").textContent = session.last_error || "";
  $("report-summary").textContent = JSON.stringify(session.summary, null, 2);
  updateChart(session.samples || []);
}

function updateChart(samples) {
  const labels = samples.map((s) => new Date(s.timestamp * 1000).toLocaleTimeString());
  const values = samples.map((s) => s.value);
  if (!state.chart) {
    state.chart = new Chart($("live-chart"), {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "métrica",
            data: values,
            borderColor: "#0f3d5c",
            tension: 0.2,
            pointRadius: 0,
          },
        ],
      },
      options: {
        animation: false,
        plugins: { legend: { display: false } },
        scales: { x: { display: false } },
      },
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
    updateLive(session);
  };
}

async function startMeasure() {
  const res = await fetch(`/api/sessions/${state.sessionId}/start`, { method: "POST" });
  const data = await res.json();
  if (!res.ok) {
    $("live-error").textContent = data.detail || "Falha ao iniciar";
    return;
  }
  $("btn-start").disabled = true;
  $("btn-stop").disabled = false;
  updateLive(data);
  startStream();
  gotoStep(3);
}

async function stopMeasure() {
  const res = await fetch(`/api/sessions/${state.sessionId}/stop`, { method: "POST" });
  const data = await res.json();
  $("btn-start").disabled = false;
  $("btn-stop").disabled = true;
  if (state.es) {
    state.es.close();
    state.es = null;
  }
  updateLive(data);
  gotoStep(4);
}

document.querySelectorAll(".step").forEach((btn) => {
  btn.addEventListener("click", () => {
    if (!btn.disabled) gotoStep(Number(btn.dataset.step));
  });
});

$("btn-load-example").addEventListener("click", () => loadExample().catch(console.error));
$("btn-validate").addEventListener("click", () =>
  validateRequirement().catch((e) => {
    $("validate-out").textContent = String(e);
  })
);
$("btn-create-session").addEventListener("click", () =>
  createSession().catch((e) => {
    $("validate-out").textContent = String(e);
  })
);
$("btn-recreate").addEventListener("click", () =>
  createSession().catch((e) => {
    $("validate-out").textContent = String(e);
  })
);
$("btn-goto-measure").addEventListener("click", () => gotoStep(3));
$("btn-start").addEventListener("click", () => startMeasure().catch(console.error));
$("btn-stop").addEventListener("click", () => stopMeasure().catch(console.error));

loadExample();
