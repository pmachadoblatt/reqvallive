"""Relatório HTML — procedimento de V&V + evidência auditável."""

from __future__ import annotations

import html
import json as _json
from datetime import datetime, timezone

from reqvallive.eval.live import constraint_text, metric_name
from reqvallive.metrics.registry import DISTANCE_METRICS
from reqvallive.models.session import MeasurementSession


def _ok_label(ok: bool | None) -> tuple[str, str]:
    if ok is True:
        return "PASS", "pass"
    if ok is False:
        return "FAIL", "fail"
    return "PENDENTE", "na"


def _fmt(v: float | None, unit: str = "") -> str:
    if v is None:
        return "—"
    u = f" {html.escape(unit)}" if unit else ""
    return f"{v:g}{u}"


def _fmt_ts(ts: float | None) -> str:
    if ts is None:
        return "—"
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%H:%M:%S")


def _fmt_dt(ts: float | None) -> str:
    if ts is None:
        return "—"
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _duration_text(started: float | None, ended: float | None, measuring: bool) -> str:
    if started is None:
        return "—"
    if ended is None:
        return "em curso" if measuring else "—"
    secs = max(0.0, ended - started)
    if secs < 60:
        return f"{secs:.0f} s"
    mins, rem = divmod(int(secs), 60)
    if mins < 60:
        return f"{mins} min {rem} s"
    hours, mins = divmod(mins, 60)
    return f"{hours} h {mins} min"


def _vv_methods(session: MeasurementSession) -> str:
    methods: list[str] = []
    for req in session.active_requirements():
        vv = getattr(req.vv_method, "value", None) or str(req.vv_method or "")
        if vv and vv not in methods:
            methods.append(vv)
    return ", ".join(methods) if methods else "—"


def _gate_for_report(session: MeasurementSession) -> dict:
    """Prefere o gate congelado no snapshot; senão o gate actual da sessão."""
    snap = session.approved_sc_snapshot or {}
    gate = snap.get("gate")
    if isinstance(gate, dict):
        return gate
    if session.criteria_gate is not None:
        return session.criteria_gate.to_dict()
    return {}


def _procedure_section(session: MeasurementSession) -> str:
    gate = _gate_for_report(session)
    gate_status = html.escape(str(gate.get("global_status") or "—"))
    accepted = gate.get("accepted_count", "—")
    rejected = gate.get("rejected_count", "—")
    warnings = gate.get("warning_count", "—")
    methods = html.escape(_vv_methods(session))

    rows = []
    for r in gate.get("results") or []:
        st = html.escape(str(r.get("status") or "—"))
        klass = "pass" if r.get("status") == "ACCEPT" else ("fail" if r.get("status") == "REJECT" else "na")
        err_n = r.get("error_count", 0)
        warn_n = r.get("warning_count", 0)
        rows.append(
            f"<tr class='{klass}'>"
            f"<td>{html.escape(str(r.get('req_id') or ''))}</td>"
            f"<td><strong>{st}</strong></td>"
            f"<td>{html.escape(str(r.get('vv_method') or '—'))}</td>"
            f"<td><code>{html.escape(str(r.get('metric') or '—'))}</code></td>"
            f"<td>{html.escape(str(r.get('criteria_type') or '—'))}</td>"
            f"<td>{err_n} erro(s) · {warn_n} aviso(s)</td>"
            "</tr>"
        )

    theory = gate.get("theory_refs") or []
    theory_html = ""
    if theory:
        items = "".join(f"<li>{html.escape(str(t))}</li>" for t in theory)
        theory_html = f"<ul class='meta refs'>{items}</ul>"

    return f"""
<div class="card" id="procedimento-vv">
  <h2>1. Procedimento de V&amp;V</h2>
  <p class="muted">Método declarado e aprovação do Success Criteria <em>antes</em> da medição
     (MSFC / SIS-08 Methods).</p>
  <dl class="proc">
    <dt>Método V&amp;V</dt><dd><code>{methods}</code></dd>
    <dt>Gate global</dt><dd><strong class="{'pass' if gate.get('global_status')=='ACCEPT' else 'fail'}">{gate_status}</strong>
      · aceites: {accepted} · rejeitados: {rejected} · avisos: {warnings}</dd>
    <dt>Pode medir?</dt><dd>{"Sim — critério aprovado para evidência live MQTT"
      if gate.get("global_status") == "ACCEPT" or gate.get("can_start_measurement")
      else "Não — medição bloqueada até ACCEPT"}</dd>
  </dl>
  <table><thead><tr>
    <th>Requisito</th><th>Gate</th><th>Método</th><th>Métrica</th><th>Tipo SC</th><th>Motivos</th>
  </tr></thead>
  <tbody>{''.join(rows) or '<tr><td colspan=6>—</td></tr>'}</tbody></table>
  {theory_html}
</div>"""


def _measurement_conditions_section(session: MeasurementSession, summary: dict) -> str:
    snap = session.approved_sc_snapshot or {}
    mqtt = snap.get("mqtt") if isinstance(snap.get("mqtt"), dict) else {}
    broker = html.escape(str(mqtt.get("broker") or session.mqtt_broker))
    port = mqtt.get("port") if mqtt.get("port") is not None else session.mqtt_port
    topic = html.escape(str(mqtt.get("topic") or session.mqtt_topic))
    user = html.escape(session.mqtt_username or "—")
    duration = _duration_text(session.started_at, session.ended_at, session.measuring)
    state = (
        "ENCERRADA"
        if session.measurement_ended
        else ("A MEDIR" if session.measuring else "não iniciada")
    )
    drones = ", ".join(sorted(session.drones.keys())) or "—"

    return f"""
<div class="card" id="condicoes-medicao">
  <h2>2. Condições de medição</h2>
  <p class="muted">Protocolo, tópico e janela temporal da evidência coletada.</p>
  <dl class="proc">
    <dt>Protocolo</dt><dd>MQTT (Paho) · QoS conforme subscriber da sessão</dd>
    <dt>Broker</dt><dd><code>{broker}:{port}</code></dd>
    <dt>Tópico</dt><dd><code>{topic}</code></dd>
    <dt>Utilizador MQTT</dt><dd><code>{user}</code> <span class="muted">(senha omitida)</span></dd>
    <dt>Sessão</dt><dd><code>{html.escape(session.id)}</code></dd>
    <dt>Criada em</dt><dd>{_fmt_dt(session.created_at)}</dd>
    <dt>Início medição</dt><dd>{_fmt_dt(session.started_at)}</dd>
    <dt>Fim medição</dt><dd>{_fmt_dt(session.ended_at) if session.ended_at else ("em curso" if session.measuring else "—")}</dd>
    <dt>Duração</dt><dd>{html.escape(duration)} · estado: <strong>{state}</strong></dd>
    <dt>Entidades</dt><dd>{summary.get("drone_count", 0)} drone(s): {html.escape(drones)}</dd>
    <dt>Amostras</dt><dd>{summary.get("message_count", 0)} mensagens MQTT ·
      {summary.get("sample_count", 0)} amostras registadas na janela</dd>
    <dt>Métricas pedidas</dt><dd><code>{html.escape(", ".join(summary.get("tracked_metrics") or session.tracked_metrics()) or "—")}</code></dd>
  </dl>
</div>"""


def _snapshot_section(session: MeasurementSession) -> str:
    snap = session.approved_sc_snapshot
    if not snap:
        return (
            '<div class="card" id="snapshot-sc"><h2>3. Success Criteria aprovado (snapshot)</h2>'
            '<p class="muted">Ainda sem snapshot — o SC é congelado ao iniciar a medição.</p></div>'
        )
    frozen = _fmt_dt(snap.get("frozen_at"))
    gate_st = html.escape(str(snap.get("gate_status") or "—"))
    rows = []
    for req in snap.get("requirements") or []:
        sc = req.get("success_criteria") or {}
        sc_pretty = html.escape(_json.dumps(sc, ensure_ascii=False, indent=2))
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(req.get('req_id') or ''))}</td>"
            f"<td>{html.escape(str(req.get('title') or ''))}</td>"
            f"<td>{html.escape(str(req.get('text') or ''))}</td>"
            f"<td>{html.escape(str(req.get('vv_method') or ''))}</td>"
            f"<td><pre class='sc-json'>{sc_pretty}</pre></td>"
            "</tr>"
        )
    return f"""
<div class="card" id="snapshot-sc">
  <h2>3. Success Criteria aprovado (snapshot)</h2>
  <p class="meta">Congelado em <strong>{frozen}</strong> · gate <strong>{gate_st}</strong>
     · sessão <code>{html.escape(str(snap.get('session_id') or ''))}</code></p>
  <p class="muted">Cópia imutável do critério que valeu nesta corrida
     (não muda se o requisito de trabalho for alterado depois).</p>
  <table><thead><tr>
    <th>ID</th><th>Título</th><th>Texto</th><th>Método</th><th>success_criteria</th>
  </tr></thead>
  <tbody>{''.join(rows) or '<tr><td colspan=5>—</td></tr>'}</tbody></table>
</div>"""


def build_html_report(session: MeasurementSession) -> str:
    summary = session.summary()
    findings = session.findings()
    overall = summary.get("overall_ok")
    verdict, verdict_class = _ok_label(overall if isinstance(overall, bool) else None)
    if overall is None:
        verdict, verdict_class = "INCONCLUSIVO", "na"

    tracked = summary.get("tracked_metrics") or session.tracked_metrics()
    show_battery = any("batter" in str(m).lower() or m == "remainingCharge" for m in tracked)

    note = (
        "<p class='note'>O resultado usa âmbito <strong>all_timesteps</strong>: "
        "se qualquer amostra violar o limiar, o requisito fica <strong>FAIL</strong> até ao fim. "
        "A tabela mostra o valor <em>atual</em> (último), o <em>mínimo</em> da corrida e a "
        "<em>1ª violação</em> — para não confundir o número «travado» do fail com o valor presente.</p>"
    )

    fail_cards = []
    pass_cards = []
    pending_cards = []
    for f in findings:
        label, klass = _ok_label(f.get("ok"))
        unit = f.get("unit") or ""
        entities_html = ""
        ents = f.get("entities") or []
        if ents:
            rows = []
            for e in ents:
                el, ek = _ok_label(e.get("ok"))
                rows.append(
                    f"<tr class='{ek}'>"
                    f"<td>{html.escape(str(e.get('id')))}</td>"
                    f"<td>{_fmt(e.get('last'), unit)}</td>"
                    f"<td>{_fmt(e.get('min'), unit)}</td>"
                    f"<td>{_fmt(e.get('max'), unit)}</td>"
                    f"<td>{_fmt(e.get('first_fail'), unit)}</td>"
                    f"<td>{_fmt_ts(e.get('first_fail_ts'))}</td>"
                    f"<td>{e.get('fail_count', 0)} / {e.get('sample_count', 0)}</td>"
                    f"<td><strong>{el}</strong></td>"
                    f"</tr>"
                )
            entities_html = (
                "<table class='mini'><thead><tr>"
                "<th>Drone</th><th>Atual</th><th>Mín</th><th>Máx</th>"
                "<th>1ª violação</th><th>Hora</th><th>Falhas / amostras</th><th>Resultado</th>"
                "</tr></thead>"
                f"<tbody>{''.join(rows)}</tbody></table>"
            )

        card = f"""
        <div class="finding {klass}">
          <div class="finding-head">
            <span class="badge {klass}">{label}</span>
            <strong>{html.escape(f.get('req_id') or '')}</strong>
            — {html.escape(f.get('title') or '')}
          </div>
          <p class="why">{html.escape(f.get('why') or '')}</p>
          <dl>
            <dt>Métrica</dt><dd><code>{html.escape(str(f.get('metric')))}</code></dd>
            <dt>Esperado</dt><dd><code>{html.escape(str(f.get('expected')))}</code></dd>
            <dt>Observado</dt><dd>{_fmt(f.get('actual'), unit) if f.get('actual') is not None else "ver tabela por drone"}</dd>
            <dt>Âmbito</dt><dd>{html.escape(str(f.get('scope')))} (todas as amostras)</dd>
          </dl>
          {entities_html}
        </div>"""
        if f.get("ok") is False:
            fail_cards.append(card)
        elif f.get("ok") is True:
            pass_cards.append(card)
        else:
            pending_cards.append(card)

    generated = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    summary_rows = []
    for f in findings:
        label, klass = _ok_label(f.get("ok"))
        summary_rows.append(
            f"<tr class='{klass}'><td>{html.escape(f.get('req_id') or '')}</td>"
            f"<td>{html.escape(f.get('title') or '')}</td>"
            f"<td><code>{html.escape(str(f.get('metric')))}</code></td>"
            f"<td><code>{html.escape(str(f.get('expected')))}</code></td>"
            f"<td><strong>{label}</strong></td>"
            f"<td>{html.escape(f.get('why') or '')}</td></tr>"
        )

    msg_headers = ["Hora", "Drone"] + [html.escape(m) for m in tracked] + ["Estado", "Lat", "Lon"]
    msg_rows = []
    for m in session.message_log[-50:]:
        ts = datetime.fromtimestamp(m["ts"], tz=timezone.utc).strftime("%H:%M:%S")
        viol = bool(m.get("violation"))
        cells = [ts, html.escape(str(m.get("drone")))]
        for metric in tracked:
            val = m.get(metric)
            cells.append("—" if val is None else str(val))
        cells.append("VIOLAÇÃO" if viol else "ok")
        cells.append(str(m.get("lat") if m.get("lat") is not None else "—"))
        cells.append(str(m.get("lon") if m.get("lon") is not None else "—"))
        cls = " class='sample-fail'" if viol else ""
        msg_rows.append(f"<tr{cls}>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")

    bat_li = ""
    if show_battery:
        bat_li = (
            f"<li>Bateria min/max na medição: {summary.get('min_battery')} / "
            f"{summary.get('max_battery')}</li>"
        )
    sep_li = ""
    if any(m in DISTANCE_METRICS for m in tracked):
        sep_li = f"<li>Separação mínima observada: {summary.get('min_separation_m')}</li>"

    procedure_html = _procedure_section(session)
    conditions_html = _measurement_conditions_section(session, summary)
    snapshot_html = _snapshot_section(session)

    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"/>
<title>Relatório ReqValLive — {verdict}</title>
<style>
:root {{ --bg:#f4f6f8; --card:#fff; --ink:#16202a; --muted:#5a6a7a; --line:#e2e8ee;
  --pass:#0a7a2f; --fail:#b00020; --na:#6b7280; --pass-bg:#e8f7ee; --fail-bg:#fde8ec; --na-bg:#f3f4f6; }}
body{{font-family:"Segoe UI",system-ui,sans-serif;margin:0;background:var(--bg);color:var(--ink);line-height:1.45}}
.wrap{{max-width:1040px;margin:0 auto;padding:1.5rem}}
.hero{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:1.5rem;margin-bottom:1rem}}
.verdict{{font-size:2rem;font-weight:750;letter-spacing:.02em}}
.pass{{color:var(--pass)}}.fail{{color:var(--fail)}}.na{{color:var(--na)}}
.meta{{color:var(--muted);font-size:.95rem}}
.note{{background:#fffbeb;border:1px solid #f6d98b;border-radius:8px;padding:.75rem 1rem;font-size:.9rem}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:.75rem;margin-top:1rem}}
.stat{{background:var(--bg);border-radius:8px;padding:.75rem}}
.stat b{{display:block;font-size:1.4rem}}
h2{{margin:0 0 .75rem;font-size:1.15rem}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:1rem;margin-bottom:1rem}}
.finding{{border:1px solid var(--line);border-radius:10px;padding:1rem;margin:.75rem 0;background:#fff}}
.finding.fail{{background:var(--fail-bg);border-color:#f0b4bf}}
.finding.pass{{background:var(--pass-bg);border-color:#b7e4c7}}
.finding.na{{background:var(--na-bg)}}
.finding-head{{display:flex;gap:.6rem;align-items:center;flex-wrap:wrap;margin-bottom:.35rem}}
.badge{{font-size:.75rem;font-weight:700;padding:.2rem .5rem;border-radius:4px;background:#fff;border:1px solid currentColor}}
.why{{font-size:1.02rem;margin:.4rem 0 .8rem}}
dl{{display:grid;grid-template-columns:140px 1fr;gap:.25rem .75rem;margin:0;font-size:.92rem}}
dl.proc{{grid-template-columns:160px 1fr;margin:.75rem 0 1rem}}
dt{{color:var(--muted)}} dd{{margin:0}}
table{{width:100%;border-collapse:collapse;font-size:.88rem}}
th,td{{border-bottom:1px solid var(--line);padding:.4rem .45rem;text-align:left;vertical-align:top}}
tr.fail td:last-child, tr.fail strong{{color:var(--fail)}}
tr.pass td:last-child, tr.pass strong{{color:var(--pass)}}
tr.sample-fail{{background:#fde8ec}}
tr.sample-fail td{{color:var(--fail)}}
code{{background:#eef2f6;padding:.1rem .35rem;border-radius:4px;font-size:.88em}}
.sc-json{{margin:0;white-space:pre-wrap;font-size:.8rem;background:#eef2f6;padding:.5rem;border-radius:6px;max-width:420px}}
.mini{{margin-top:.75rem;background:rgba(255,255,255,.65)}}
.muted{{color:var(--muted)}}
.toc{{font-size:.9rem;margin:.75rem 0 0;padding-left:1.2rem}}
.toc a{{color:inherit}}
.refs{{font-size:.85rem}}
@media (max-width:700px){{.grid{{grid-template-columns:1fr}} dl,dl.proc{{grid-template-columns:1fr}}}}
</style></head><body><div class="wrap">
<div class="hero">
  <div class="verdict {verdict_class}">{verdict}</div>
  <p class="meta">Relatório de procedimento ReqValLive · gerado {generated}</p>
  <p class="meta">Sessão <code>{html.escape(session.id)}</code>
     · método <code>{html.escape(_vv_methods(session))}</code>
     · gate <strong>{html.escape(str((_gate_for_report(session) or {}).get("global_status") or "—"))}</strong></p>
  <div class="grid">
    <div class="stat"><span class="muted">Requisitos OK</span><b class="pass">{summary.get("reqs_pass", 0)}</b></div>
    <div class="stat"><span class="muted">Requisitos FAIL</span><b class="fail">{summary.get("reqs_fail", 0)}</b></div>
    <div class="stat"><span class="muted">Pendentes</span><b class="na">{summary.get("reqs_pending", 0)}</b></div>
  </div>
  <ul class="meta">
    <li>Drones: {summary.get("drone_count")} · Mensagens: {summary.get("message_count")}</li>
    <li>Métricas: <code>{html.escape(", ".join(tracked) or "—")}</code></li>
    {bat_li}{sep_li}
  </ul>
  <ol class="toc">
    <li><a href="#procedimento-vv">Procedimento de V&amp;V</a></li>
    <li><a href="#condicoes-medicao">Condições de medição</a></li>
    <li><a href="#snapshot-sc">Success Criteria aprovado (snapshot)</a></li>
    <li><a href="#resultados">Resultados (esperado × observado)</a></li>
    <li><a href="#amostras">Últimas amostras MQTT</a></li>
  </ol>
  {note}
</div>

{procedure_html}
{conditions_html}
{snapshot_html}

<div class="card" id="resultados">
  <h2>4. Resultados — esperado × observado</h2>
  <p class="muted">Veredicto por requisito com evidência da corrida (1ª violação, min/máx, contagens).</p>
  <table><thead><tr>
    <th>ID</th><th>Título</th><th>Métrica</th><th>Esperado</th><th>Resultado</th><th>Porquê</th>
  </tr></thead>
  <tbody>{''.join(summary_rows) or '<tr><td colspan=6>—</td></tr>'}</tbody></table>
</div>

{f'<div class="card"><h2>Evidência das falhas</h2>{"".join(fail_cards)}</div>' if fail_cards else ''}
{f'<div class="card"><h2>O que passou</h2>{"".join(pass_cards)}</div>' if pass_cards else ''}
{f'<div class="card"><h2>Pendentes</h2>{"".join(pending_cards)}</div>' if pending_cards else ''}

<div class="card" id="amostras">
  <h2>5. Últimas amostras MQTT</h2>
  <p class="muted">Linhas vermelhas = amostra que violou o limiar naquele instante.</p>
  <table><thead><tr>{''.join(f"<th>{h}</th>" for h in msg_headers)}</tr></thead>
  <tbody>{''.join(msg_rows) or '<tr><td colspan="' + str(len(msg_headers)) + '">—</td></tr>'}</tbody></table>
</div>
</div></body></html>"""
