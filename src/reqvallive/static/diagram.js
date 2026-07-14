/** Diagrama SysML visual com caixas coloridas (estilo Magic). */
window.ReqValDiagram = {
  render(container, session) {
    if (!container) return;
    const reqs = session.requirements || [];
    const drones = session.drones || [];
    const overall = session.overall_ok;
    const topic = session.mqtt_topic || "—";

    const droneBoxes = (drones.length ? drones : [{ id: "droneA" }, { id: "droneB" }, { id: "droneC" }])
      .slice(0, 6)
      .map((d) => {
        const bat = d.battery ?? "—";
        const oks = d.ok_by_req || {};
        const flags = Object.values(oks);
        let klass = "part-box";
        if (flags.length && flags.every((v) => v === true)) klass += " pass";
        if (flags.length && flags.some((v) => v === false)) klass += " fail";
        const satInner = reqs
          .map((r) => {
            const ok = oks[r.req_id];
            const okLabel = ok === true ? "true" : ok === false ? "false" : "—";
            const tip =
              r.success_criteria?.type === "threshold"
                ? `threshold=${r.success_criteria.value} · actual=${d.metrics?.[r.metric] ?? bat}`
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
            <div class="muted">${d.latitude != null ? `${d.latitude.toFixed?.(5) ?? d.latitude}, ${d.longitude}` : "sem posição"}</div>
            ${satInner}
          </div>
        </div>`;
      })
      .join("");

    const reqBoxes = reqs
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

    const sep = session.global_metrics?.min_separation_m;
    const verif = `<div class="ver-box">
      <div class="box-title ver">«verification» VerifyMission</div>
      <div class="box-body">
        <div>objective: verify requisitos da missão</div>
        <div>MQTT topic: <code>${escapeHtml(topic)}</code></div>
        <div>min_separation_m: <strong>${sep ?? "—"}</strong></div>
        <div>overall: <strong class="${overall === true ? "ok" : overall === false ? "nok" : ""}">${
          overall === true ? "PASS" : overall === false ? "FAIL" : "—"
        }</strong></div>
      </div>
    </div>`;

    container.innerHTML = `
      <div class="magic-board">
        <div class="board-label">«view» Solution Architecture</div>
        <div class="board-row parts">${droneBoxes || '<div class="muted">Instâncias de drone aparecem ao receber MQTT</div>'}</div>
        <div class="board-row reqs">${reqBoxes}</div>
        <div class="board-row">${verif}</div>
      </div>`;
  },
};

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
