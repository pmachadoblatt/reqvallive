const state = { sessionId: null, es: null, chart: null, defaults: null, frozen: false, scModel: null };

const $ = (id) => document.getElementById(id);

function on(id, event, handler) {
  const el = $(id);
  if (!el) {
    console.warn(`[ReqValLive] elemento #${id} não encontrado — skip ${event}`);
    return;
  }
  el.addEventListener(event, handler);
}

const SAMPLE_MD = `# Requisitos de missão (modelo Success Criteria)

## RQ-BAT-001 — Bateria mínima (system / test)
O sistema deve manter **batteryLevel >= 20 percent** em **cada drone** durante a operação (scope: all_entities).

- Success Criteria (Performance): threshold metric=batteryLevel operator=>= value=20 unit=percent tolerance=0
- Environment: voo outdoor; telemetria MQTT activa
- Restrictions / localization: all_entities (por aeronave)
- Specifications: conops_ref CONOPS-UTM §4.2; vv_method=test
- Checkpoints: amostragem contínua enquanto measuring=true

## RQ-SEP-001 — Separação mínima (system / test)
Separação Haversine entre quaisquer dois drones: **min_separation_m >= 20 meters** (métrica global).

- Success Criteria: threshold metric=min_separation_m operator=>= value=20 unit=meters scope=all_entities
- Pré-condição: ≥2 drones com GPS
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

async function loadCriteriaModel() {
  try {
    const res = await fetch("/api/criteria/model");
    state.scModel = await res.json();
    renderCriteriaModel(state.scModel);
  } catch (e) {
    if ($("sc-md-example")) {
      $("sc-md-example").textContent = SAMPLE_MD;
    }
  }
}

function renderCriteriaModel(model) {
  if (!model) return;
  const life = $("sc-lifecycle");
  if (life) {
    life.innerHTML = (model.lifecycle || []).map((s) => `<li>${escapeHtml(s)}</li>`).join("");
  }
  const dims = $("sc-dimensions");
  if (dims) {
    dims.innerHTML = (model.msfc_dimensions || [])
      .map(
        (d) =>
          `<div class="sc-dim"><strong>${escapeHtml(d.name)}</strong><span class="muted">${escapeHtml(d.ask)}</span></div>`
      )
      .join("");
  }
  const methods = $("sc-methods");
  if (methods && model.method_coherence) {
    methods.innerHTML = Object.entries(model.method_coherence)
      .map(([k, v]) => `<li><code>${escapeHtml(k)}</code> — ${escapeHtml(v)}</li>`)
      .join("");
  }
  if ($("sc-md-example")) $("sc-md-example").textContent = model.markdown_example || SAMPLE_MD;
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function renderGatePreview(session, targetId) {
  const el = $(targetId || "gate-preview");
  if (!el) return;
  const g = session?.criteria_gate;
  if (!g) {
    el.className = "gate-preview muted hidden";
    el.textContent = "";
    return;
  }
  el.classList.remove("hidden");
  const ok = g.global_status === "ACCEPT";
  const warnN = g.warning_count || 0;
  el.className = `gate-preview ${ok ? (warnN ? "accept-warn" : "accept") : "reject"}`;

  const blocks = (g.results || []).map((r) => {
    const errs = (r.reasons || []).filter((x) => x.severity === "error");
    const warns = (r.reasons || []).filter((x) => x.severity === "warning");
    const head = `<div class="gate-req"><strong>${escapeHtml(r.status)}</strong> ${escapeHtml(r.req_id)}
      <span class="muted">· ${escapeHtml(r.vv_method || "?")} · ${escapeHtml(r.metric || "?")}</span></div>`;
    let body = "";
    if (errs.length) {
      body += `<ul class="gate-list errors">${errs
        .map(
          (e) =>
            `<li><code>${escapeHtml(e.code)}</code> ${escapeHtml(e.message)}${
              e.suggestion ? `<div class="muted tip">→ ${escapeHtml(e.suggestion)}</div>` : ""
            }</li>`
        )
        .join("")}</ul>`;
    }
    if (warns.length) {
      body += `<div class="gate-warn-label">Avisos (não bloqueiam a medição — critério ainda incompleto face à MSFC)</div>
        <ul class="gate-list warnings">${warns
          .map(
            (w) =>
              `<li><code>${escapeHtml(w.code)}</code> ${escapeHtml(w.message)}${
                w.suggestion ? `<div class="muted tip">→ ${escapeHtml(w.suggestion)}</div>` : ""
              }</li>`
          )
          .join("")}</ul>`;
    }
    if (r.status === "ACCEPT" && !warns.length) {
      body += `<p class="muted">Critério completo o suficiente para medição live.</p>`;
    }
    return head + body;
  });

  const title = ok
    ? warnN
      ? `Aprovado com ${warnN} aviso(s) — pode medir, mas o critério pode ser enriquecido`
      : `Aprovado — pode seguir para MQTT / medição`
    : `Recusado — medição bloqueada até corrigir`;

  el.innerHTML =
    `<div class="gate-title">${escapeHtml(g.global_status)} — ${escapeHtml(title)}</div>` +
    `<div class="muted">${g.accepted_count} ACCEPT · ${g.rejected_count} REJECT · ${warnN} avisos</div>` +
    blocks.join("");
}

function openScModal() {
  const modal = $("sc-modal");
  if (modal) modal.classList.remove("hidden");
}

function closeScModal() {
  const modal = $("sc-modal");
  if (modal) modal.classList.add("hidden");
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

function trackedMetrics(session) {
  if (session.tracked_metrics?.length) return session.tracked_metrics;
  return (session.requirements || []).map((r) => r.metric).filter(Boolean);
}

function isBatteryMetric(m) {
  return /batter|remainingCharge/i.test(String(m || ""));
}

function formatMetricLine(drone, metrics) {
  if (!metrics.length) return "—";
  return metrics
    .map((m) => {
      if (/separation|min_separation/i.test(m)) return null;
      const v = drone.metrics?.[m] ?? (isBatteryMetric(m) ? drone.battery : null);
      return `${m}=${v ?? "—"}`;
    })
    .filter(Boolean)
    .join(" · ");
}

function renderSession(session) {
  state.sessionId = session.id;
  state.frozen = !!session.measurement_ended;
  const draw = () => {
    if (window.ReqValDiagram) {
      window.ReqValDiagram.render($("sysml-canvas"), session);
      window.ReqValDiagram.render($("sysml-live"), session);
    }
  };
  if (window.mermaid) draw();
  else setTimeout(draw, 300);
  if ($("sysml-preview")) $("sysml-preview").textContent = session.sysml_preview || "";
  if ($("btn-dl-sysml")) $("btn-dl-sysml").href = `/api/sessions/${session.id}/sysml`;
  if ($("btn-dl-md")) $("btn-dl-md").href = `/api/sessions/${session.id}/model.md`;
  if ($("btn-report")) $("btn-report").href = `/api/sessions/${session.id}/report`;
  updateMonitor(session);
  renderGatePreview(session, "gate-preview");
  renderGatePreview(session, "gate-panel-2");
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

function measurePill(session) {
  if (session.measurement_ended) return "medição encerrada";
  if (session.measuring) return "a medir";
  return "aguardando início";
}

function updateMonitor(session) {
  // Após encerrar, ignora updates SSE que mudariam o estado congelado
  if (state.frozen && !session.measurement_ended && session.measuring) {
    return;
  }
  if (session.measurement_ended) state.frozen = true;
  if (session.measuring) state.frozen = false;

  if ($("mqtt-status-pill")) {
    $("mqtt-status-pill").textContent =
      `${statusLabel(session.mqtt_status)} · ${measurePill(session)}`;
  }
  if ($("conn-pill")) {
    $("conn-pill").textContent = session.connected
      ? `conectado · ${measurePill(session)}`
      : statusLabel(session.mqtt_status);
  }
  if ($("btn-start-monitor")) {
    $("btn-start-monitor").disabled = !session.connected && session.mqtt_status === "disconnected";
  }
  if ($("btn-stop-monitor")) {
    $("btn-stop-monitor").disabled = !session.measuring && !session.measurement_ended;
    if (session.measurement_ended) $("btn-stop-monitor").textContent = "Medição encerrada";
    else $("btn-stop-monitor").textContent = "Encerrar medição";
  }

  const metrics = trackedMetrics(session);
  const reqs = session.requirements || [];
  const primary = reqs[0];
  const primaryId = primary?.req_id;

  // Veredicto live
  const lv = $("live-verdict");
  const vp = $("verdict-pill");
  if (lv) {
    const ov = session.overall_ok;
    if (!session.measuring && !session.measurement_ended) {
      lv.className = "live-verdict muted";
      lv.textContent = "Aguardando início da medição…";
      if (vp) vp.textContent = "—";
    } else if (ov === true) {
      lv.className = "live-verdict pass";
      lv.textContent = "PASS — todos os drones cumprem o critério em todas as amostras até agora.";
      if (vp) { vp.textContent = "PASS"; vp.className = "pill pass-pill"; }
    } else if (ov === false) {
      const fails = (session.findings || []).filter((f) => f.ok === false);
      const bits = fails
        .flatMap((f) => (f.entities || []).filter((e) => e.ok === false))
        .map((e) => `${e.id}: min=${e.min ?? "—"} 1ª=${e.first_fail ?? "—"} atual=${e.last ?? "—"}`)
        .join(" · ");
      lv.className = "live-verdict fail";
      lv.textContent =
        "FAIL — houve violação (latched). Valores atuais continuam a actualizar. " +
        (bits || (session.findings || []).map((f) => f.why).join(" "));
      if (vp) { vp.textContent = "FAIL"; vp.className = "pill fail-pill"; }
    } else {
      lv.className = "live-verdict muted";
      lv.textContent = "A medir… a aguardar amostras suficientes.";
      if (vp) { vp.textContent = "…"; vp.className = "pill"; }
    }
  }

  const stats = $("drone-stats");
  if (stats) {
    stats.innerHTML = (session.drones || [])
      .map((d) => {
        const rid = primaryId;
        const latched = rid ? d.ok_by_req?.[rid] : null;
        const last = rid ? d.last_actual_by_req?.[rid] : d.battery;
        const minV = rid ? d.min_actual_by_req?.[rid] : null;
        const first = rid ? d.fail_actual_by_req?.[rid] : null;
        const nFail = rid ? d.fail_count_by_req?.[rid] || 0 : 0;
        const nSamp = rid ? d.sample_count_by_req?.[rid] || 0 : 0;
        const badge =
          latched === true ? "PASS" : latched === false ? "FAIL" : "—";
        const klass =
          latched === true ? "drone-card pass" : latched === false ? "drone-card fail" : "drone-card";
        const metric = primary?.metric || metrics[0] || "metric";
        return `<div class="${klass}">
          <div class="drone-head"><strong>${d.id}</strong><span class="badge ${
            latched === true ? "pass" : latched === false ? "fail" : ""
          }">${badge}</span></div>
          <div class="drone-metrics">
            <span><em>atual</em> ${last ?? "—"}</span>
            <span><em>mín</em> ${minV ?? "—"}</span>
            <span><em>1ª falha</em> ${first ?? "—"}</span>
            <span><em>falhas</em> ${nFail}/${nSamp}</span>
          </div>
          <div class="muted">${metric}${
            d.latitude != null
              ? ` · ${Number(d.latitude).toFixed(5)}, ${Number(d.longitude).toFixed(5)}`
              : ""
          }</div>
        </div>`;
      })
      .join("") || '<div class="muted">Nenhum drone ainda</div>';

    const sep = session.global_metrics?.min_separation_m;
    if (sep != null && metrics.some((m) => /separation|min_separation/i.test(m))) {
      const gok = primary ? session.requirements?.find((r) => r.req_id === primaryId)?.global_ok : null;
      // global_ok is on requirements in public dict
      const gReq = (session.requirements || []).find((r) => /separation/i.test(r.metric || ""));
      const gStatus = gReq?.global_ok;
      stats.innerHTML +=
        `<div class="drone-card ${gStatus === false ? "fail" : gStatus === true ? "pass" : ""}">
          <div class="drone-head"><strong>Global</strong>
          <span class="badge ${gStatus === false ? "fail" : gStatus === true ? "pass" : ""}">${
            gStatus === true ? "PASS" : gStatus === false ? "FAIL" : "—"
          }</span></div>
          <div>min_separation_m = <strong>${Number(sep).toFixed(2)}</strong> m</div>
        </div>`;
    }
  }

  const feed = $("msg-feed");
  if (feed) {
    feed.innerHTML = (session.message_log || [])
      .slice()
      .reverse()
      .map((m) => {
        const t = new Date(m.ts * 1000).toLocaleTimeString();
        const parts = metrics
          .map((metric) => {
            const v = m[metric];
            return v != null ? `${metric}=${v}` : null;
          })
          .filter(Boolean);
        if (!parts.length && m.lat != null) parts.push(`lat=${m.lat}`, `lon=${m.lon}`);
        const cls = m.violation ? "msg-fail" : "";
        return `<div class="${cls}">[${t}] ${m.drone} ${parts.join(" ")}${
          m.violation ? " · VIOLAÇÃO" : ""
        }</div>`;
      })
      .join("");
  }

  const findings = session.findings || [];
  if ($("out-4")) {
    if (findings.length) {
      $("out-4").textContent = findings
        .map((f) => {
          const st = f.ok === true ? "PASS" : f.ok === false ? "FAIL" : "PENDENTE";
          return `[${st}] ${f.req_id} (${f.metric})\n  ${f.why}`;
        })
        .join("\n\n");
    } else {
      $("out-4").textContent = JSON.stringify(session.summary || {}, null, 2);
    }
  }
  if (window.ReqValDiagram) window.ReqValDiagram.render($("sysml-live"), session);
  updateChart(session);
}

function chartMetric(session) {
  const metrics = trackedMetrics(session);
  const local = metrics.find((m) => !/separation|min_separation/i.test(m));
  if (local) return local;
  if (metrics.some((m) => /separation|min_separation/i.test(m))) return "min_separation_m";
  return null;
}

function updateChart(session) {
  const canvas = $("live-chart");
  if (!canvas || typeof Chart === "undefined") return;
  const metric = chartMetric(session);
  if (!metric) {
    if (state.chart) {
      state.chart.destroy();
      state.chart = null;
    }
    return;
  }

  const thr = (session.thresholds || []).find((t) => t.metric === metric)?.success_criteria;
  const limiar = thr?.type === "threshold" ? thr.value : thr?.type === "range" ? thr.min_value : null;
  const thrLabel =
    thr?.type === "threshold"
      ? `limiar ${thr.operator} ${thr.value}`
      : thr?.type === "range"
        ? `faixa [${thr.min_value}, ${thr.max_value}]`
        : "";

  let labels;
  let values;
  let mins;
  let colors;
  let yMax = undefined;
  const primaryId = (session.requirements || [])[0]?.req_id;

  if (/separation|min_separation/i.test(metric)) {
    labels = ["atual", "1ª violação"];
    const gReq = (session.requirements || []).find((r) => /separation/i.test(r.metric || ""));
    values = [
      session.global_metrics?.min_separation_m ?? null,
      gReq?.global_actual ?? null,
    ];
    mins = null;
    colors = ["#1e3a5f", "#b91c1c"];
  } else {
    const drones = session.drones || [];
    labels = drones.map((d) => d.id.replace(/dji_mini_4_pro_?/i, ""));
    values = drones.map((d) => d.last_actual_by_req?.[primaryId] ?? d.metrics?.[metric] ?? d.battery ?? null);
    mins = drones.map((d) => d.min_actual_by_req?.[primaryId] ?? null);
    colors = drones.map((d) =>
      d.ok_by_req?.[primaryId] === false ? "#b91c1c" : "#1e3a5f"
    );
    if (isBatteryMetric(metric)) yMax = 100;
  }

  const datasets = [
    {
      label: `${metric} atual${thrLabel ? ` · ${thrLabel}` : ""}`,
      data: values,
      backgroundColor: colors,
    },
  ];
  if (mins) {
    datasets.push({
      label: "mínimo na medição",
      data: mins,
      backgroundColor: "rgba(185, 28, 28, 0.35)",
    });
  }

  if (!state.chart) {
    state.chart = new Chart(canvas, {
      type: "bar",
      data: { labels, datasets },
      options: {
        animation: false,
        plugins: { legend: { display: true } },
        scales: { y: yMax != null ? { min: 0, max: yMax } : { beginAtZero: true } },
      },
    });
  } else {
    state.chart.data.labels = labels;
    state.chart.data.datasets = datasets;
    if (state.chart.options.scales?.y) {
      if (yMax != null) {
        state.chart.options.scales.y.min = 0;
        state.chart.options.scales.y.max = yMax;
      } else {
        delete state.chart.options.scales.y.max;
        state.chart.options.scales.y.beginAtZero = true;
      }
    }
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
  if ($("out-1")) $("out-1").textContent = "Chamando LLM… (pode demorar 30–90s)";
  try {
    const res = await fetch("/api/requirements/from-markdown", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ markdown: $("md-input").value, ...mqttBody() }),
    });
    const raw = await res.text();
    let data;
    try {
      data = JSON.parse(raw);
    } catch {
      if ($("out-1")) {
        $("out-1").textContent =
          `Erro HTTP ${res.status}: resposta não-JSON do servidor.\n${raw.slice(0, 500)}`;
      }
      return;
    }
    if (!res.ok) {
      const detail = data.detail || data;
      if ($("out-1")) $("out-1").textContent = typeof detail === "string" ? detail : JSON.stringify(detail, null, 2);
      return;
    }
    if ($("out-1")) {
      const metrics = (data.tracked_metrics || []).join(", ");
      const gate = data.criteria_gate?.global_status || "?";
      const warns = data.criteria_gate?.warning_count || 0;
      $("out-1").textContent =
        `OK — ${data.requirements?.length || 0} requisito(s). Gate: ${gate}` +
        (warns ? ` (${warns} avisos)` : "") +
        `. Métricas: ${metrics || "—"}.`;
      if (warns > 0) {
        $("out-1").textContent +=
          "\nCritério aprovado para medir, mas ainda incompleto face à checklist MSFC — veja os avisos abaixo.";
      }
    }
    renderSession(data);
    if (data.criteria_gate?.global_status === "REJECT") {
      gotoStep(1);
      document.querySelector('.step[data-step="3"]').disabled = true;
      document.querySelector('.step[data-step="4"]').disabled = true;
    } else {
      gotoStep(2);
      document.querySelector('.step[data-step="3"]').disabled = false;
      document.querySelector('.step[data-step="4"]').disabled = false;
    }
  } catch (e) {
    if ($("out-1")) $("out-1").textContent = String(e);
  }
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
  const raw = await res.text();
  let data;
  try {
    data = JSON.parse(raw);
  } catch {
    if ($("out-3")) $("out-3").textContent = raw.slice(0, 400);
    return;
  }
  if (!res.ok) {
    const detail = data.detail || data;
    if ($("out-3")) {
      $("out-3").textContent =
        typeof detail === "string"
          ? detail
          : detail.message
            ? `${detail.message}\n${JSON.stringify(detail.criteria_gate || {}, null, 2)}`
            : JSON.stringify(detail, null, 2);
    }
    return;
  }
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
  state.frozen = false;
  const res = await fetch(`/api/sessions/${state.sessionId}/start`, { method: "POST" });
  const data = await res.json();
  updateMonitor(data);
  startStream();
  gotoStep(4);
}

async function stopMonitor() {
  const res = await fetch(`/api/sessions/${state.sessionId}/stop`, { method: "POST" });
  const data = await res.json();
  state.frozen = true;
  updateMonitor(data);
  if ($("out-4")) {
    const findings = data.findings || [];
    const head = data.measurement_ended
      ? "Medição encerrada — resultados congelados.\n\n"
      : "";
    $("out-4").textContent =
      head +
      findings
        .map((f) => {
          const st = f.ok === true ? "PASS" : f.ok === false ? "FAIL" : "PENDENTE";
          return `[${st}] ${f.req_id}: ${f.why}`;
        })
        .join("\n");
  }
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
    if ($("md-input")) $("md-input").value = state.scModel?.markdown_example || SAMPLE_MD;
  });
  on("btn-load-sc-model", "click", () => {
    if ($("md-input")) $("md-input").value = state.scModel?.markdown_example || SAMPLE_MD;
    closeScModal();
  });
  on("btn-open-sc-help", "click", () => openScModal());
  document.querySelectorAll("[data-close-modal]").forEach((el) => {
    el.addEventListener("click", () => closeScModal());
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
  on("btn-goto-mqtt", "click", () => {
    // só avança se gate ACCEPT
    gotoStep(3);
  });
  on("btn-connect", "click", () => applyMqttAndConnect().catch(console.error));
  on("btn-disconnect", "click", async () => {
    if (!state.sessionId) return;
    const res = await fetch(`/api/sessions/${state.sessionId}/disconnect`, { method: "POST" });
    updateMonitor(await res.json());
  });
  on("btn-start-monitor", "click", () => startMonitor().catch(console.error));
  on("btn-stop-monitor", "click", () => stopMonitor().catch(console.error));

  // Editor vazio por defeito — placeholder guia o utilizador
  loadDefaults();
  loadCriteriaModel();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bindUi);
} else {
  bindUi();
}

