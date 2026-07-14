/** Diagrama: Mermaid (UML) + caixas estilo Magic. */
window.ReqValDiagram = {
  async render(container, session) {
    if (!container) return;
    const reqs = session.requirements || [];
    const drones = session.drones || [];
    const overall = session.overall_ok;
    const topic = session.mqtt_topic || "—";
    const sep = session.global_metrics?.min_separation_m;

    const mermaidSrc = buildMermaid(session);
    container.innerHTML = `
      <div class="magic-board">
        <div class="board-label">«view» Solution Architecture</div>
        <div class="diagram-tabs">
          <span class="pill">UML (Mermaid)</span>
          <span class="muted small">Motor gratuito no browser — alternativa leve a Magic/TomSawyer</span>
        </div>
        <pre class="mermaid" id="${container.id}-mmd">${escapeHtml(mermaidSrc)}</pre>
        <div class="board-label">Instâncias / satisfy (runtime)</div>
        <div class="board-row parts">${renderDroneBoxes(drones, reqs)}</div>
        <div class="board-row reqs">${renderReqBoxes(reqs)}</div>
        <div class="board-row">${renderVerif(topic, sep, overall, reqs, session)}</div>
      </div>`;

    if (window.mermaid) {
      try {
        await window.mermaid.run({ nodes: container.querySelectorAll(".mermaid") });
      } catch (e) {
        console.warn("Mermaid render failed", e);
      }
    }
  },
};

function isDistanceMetric(metric) {
  const m = String(metric || "");
  return /separation|distance|collision/i.test(m);
}

function buildMermaid(session) {
  const reqs = session.requirements || [];
  const drones = session.drones || [];
  const lines = ["classDiagram", "direction TB"];
  lines.push('class SystemUnderTest {');
  lines.push("  +String droneName");
  lines.push("  +Real batteryLevel");
  lines.push("  +Real altitudeAGL");
  lines.push("  +Real distanceToHome");
  lines.push("  +String mqttTopic");
  lines.push("}");

  for (const r of reqs) {
    const id = safeId(r.req_id);
    const sc = r.success_criteria || {};
    lines.push(`class ${id} {`);
    lines.push("  <<requirement>>");
    lines.push(`  +metric ${r.metric || ""}`);
    if (sc.type === "threshold") {
      lines.push(`  +constraint actual ${sc.operator} ${sc.value}`);
    } else if (sc.type === "range") {
      lines.push(`  +constraint [${sc.min_value} .. ${sc.max_value}]`);
    }
    lines.push("}");
    lines.push(`SystemUnderTest ..> ${id} : satisfy`);
  }

  const shown = (drones.length ? drones : [{ id: "droneA" }, { id: "droneB" }]).slice(0, 5);
  for (const d of shown) {
    const did = safeId(d.id || "drone");
    lines.push(`class ${did} {`);
    lines.push("  <<part>>");
    lines.push(`  +battery ${d.battery ?? "—"}`);
    if (d.latitude != null) lines.push(`  +lat ${Number(d.latitude).toFixed(4)}`);
    lines.push("}");
    lines.push(`${did} --|> SystemUnderTest`);
  }

  lines.push("class VerifyMission {");
  lines.push("  <<verification>>");
  const sep = session.global_metrics?.min_separation_m;
  if (sep != null) lines.push(`  +min_separation_m ${Number(sep).toFixed(1)}`);
  lines.push(`  +overall ${session.overall_ok === true ? "PASS" : session.overall_ok === false ? "FAIL" : "PENDING"}`);
  lines.push("}");
  lines.push("VerifyMission ..> SystemUnderTest : subject");
  for (const r of reqs) {
    lines.push(`VerifyMission ..> ${safeId(r.req_id)} : verify`);
  }

  return lines.join("\n");
}

function renderDroneBoxes(drones, reqs) {
  const list = drones.length ? drones : [{ id: "droneA" }, { id: "droneB" }, { id: "droneC" }];
  return list
    .slice(0, 6)
    .map((d) => {
      const bat = d.battery ?? "—";
      const oks = d.ok_by_req || {};
      const localReqs = reqs.filter((r) => !isDistanceMetric(r.metric));
      const flags = localReqs.map((r) => oks[r.req_id]).filter((v) => v !== undefined && v !== null);
      let klass = "part-box";
      if (flags.length && flags.every((v) => v === true)) klass += " pass";
      if (flags.length && flags.some((v) => v === false)) klass += " fail";
      const satInner = localReqs
        .map((r) => {
          const ok = oks[r.req_id];
          const okLabel = ok === true ? "true" : ok === false ? "false" : "—";
          const actual = d.metrics?.[r.metric] ?? (r.metric === "batteryLevel" || r.metric === "battery_level" ? bat : "—");
          const tip =
            r.success_criteria?.type === "threshold"
              ? `threshold=${r.success_criteria.value} · actual=${actual}`
              : r.metric;
          return `<div class="sat-box ${ok === true ? "pass" : ok === false ? "fail" : ""}">
              <div class="box-title sat">«satisfy requirement» ${escapeHtml(r.req_id)}</div>
              <div class="box-body">
                <div>satisfy = <strong>${okLabel}</strong></div>
                <div class="muted">${escapeHtml(String(tip))}</div>
              </div>
            </div>`;
        })
        .join("");
      return `<div class="${klass}">
          <div class="box-title part">«part» ${escapeHtml(d.id)} :> SystemUnderTest</div>
          <div class="box-body">
            <div>batteryLevel = <strong>${bat}</strong></div>
            <div class="muted">${d.latitude != null ? `${Number(d.latitude).toFixed(5)}, ${d.longitude}` : "sem posição"}</div>
            ${satInner || '<div class="muted">sem requisito por entidade</div>'}
          </div>
        </div>`;
    })
    .join("");
}

function renderReqBoxes(reqs) {
  return reqs
    .map((r) => {
      const sc = r.success_criteria || {};
      const constraint =
        sc.type === "threshold"
          ? `{ actualValue ${sc.operator} ${sc.value} }`
          : sc.type === "range"
            ? `{ ${sc.min_value} ≤ actualValue ≤ ${sc.max_value} }`
            : "{ … }";
      return `<div class="req-box">
          <div class="box-title req">«requirement» ${escapeHtml(r.req_id)}</div>
          <div class="box-body">
            <div><strong>${escapeHtml(r.title || "")}</strong></div>
            <div class="doc">${escapeHtml(r.text || "")}</div>
            <div class="muted">subject: SystemUnderTest</div>
            <div>metric: <code>${escapeHtml(r.metric || "")}</code></div>
            <div>require constraint ${escapeHtml(constraint)}</div>
          </div>
        </div>`;
    })
    .join("");
}

function renderVerif(topic, sep, overall, reqs, session) {
  const globalSats = reqs
    .filter((r) => isDistanceMetric(r.metric))
    .map((r) => {
      const ok = session.global_ok_by_req?.[r.req_id] ?? session.requirements?.find?.(() => false);
      // from public dict requirements[].global_ok
      const reqPublic = (session.requirements || []).find((x) => x.req_id === r.req_id);
      const gok = reqPublic?.global_ok;
      const label = gok === true ? "true" : gok === false ? "false" : "—";
      return `<div class="sat-box ${gok === true ? "pass" : gok === false ? "fail" : ""}">
        <div class="box-title sat">«satisfy» ${escapeHtml(r.req_id)} (global)</div>
        <div class="box-body">satisfy = <strong>${label}</strong> · min_separation = ${sep ?? "—"}</div>
      </div>`;
    })
    .join("");

  return `<div class="ver-box">
      <div class="box-title ver">«verification» VerifyMission</div>
      <div class="box-body">
        <div>objective: verify requisitos da missão</div>
        <div>MQTT topic: <code>${escapeHtml(topic)}</code></div>
        <div>min_separation_m: <strong>${sep != null ? Number(sep).toFixed(2) : "—"}</strong></div>
        <div>overall: <strong class="${overall === true ? "ok" : overall === false ? "nok" : ""}">${
          overall === true ? "PASS" : overall === false ? "FAIL" : "—"
        }</strong></div>
        ${globalSats}
      </div>
    </div>`;
}

function safeId(text) {
  return String(text || "X").replace(/[^A-Za-z0-9_]/g, "_");
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
