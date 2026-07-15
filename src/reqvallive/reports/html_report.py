"""Relatório HTML — veredicto + evidência (atual / min / 1ª violação / #falhas)."""

from __future__ import annotations

import html
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
            <dt>Critério</dt><dd><code>{html.escape(str(f.get('expected')))}</code></dd>
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

    started = (
        datetime.fromtimestamp(session.started_at, tz=timezone.utc).strftime("%H:%M:%S")
        if session.started_at
        else "—"
    )
    ended = (
        datetime.fromtimestamp(session.ended_at, tz=timezone.utc).strftime("%H:%M:%S")
        if session.ended_at
        else ("em curso" if session.measuring else "—")
    )
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

    req_def_rows = []
    for req in session.requirements:
        req_def_rows.append(
            "<tr>"
            f"<td>{html.escape(req.req_id)}</td>"
            f"<td>{html.escape(req.title)}</td>"
            f"<td>{html.escape(req.text)}</td>"
            f"<td><code>{html.escape(constraint_text(req))}</code> "
            f"({html.escape(metric_name(req))})</td>"
            "</tr>"
        )

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
h2{{margin:1.5rem 0 .75rem;font-size:1.15rem}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:1rem;margin-bottom:1rem}}
.finding{{border:1px solid var(--line);border-radius:10px;padding:1rem;margin:.75rem 0;background:#fff}}
.finding.fail{{background:var(--fail-bg);border-color:#f0b4bf}}
.finding.pass{{background:var(--pass-bg);border-color:#b7e4c7}}
.finding.na{{background:var(--na-bg)}}
.finding-head{{display:flex;gap:.6rem;align-items:center;flex-wrap:wrap;margin-bottom:.35rem}}
.badge{{font-size:.75rem;font-weight:700;padding:.2rem .5rem;border-radius:4px;background:#fff;border:1px solid currentColor}}
.why{{font-size:1.02rem;margin:.4rem 0 .8rem}}
dl{{display:grid;grid-template-columns:140px 1fr;gap:.25rem .75rem;margin:0;font-size:.92rem}}
dt{{color:var(--muted)}} dd{{margin:0}}
table{{width:100%;border-collapse:collapse;font-size:.88rem}}
th,td{{border-bottom:1px solid var(--line);padding:.4rem .45rem;text-align:left;vertical-align:top}}
tr.fail td:last-child, tr.fail strong{{color:var(--fail)}}
tr.pass td:last-child, tr.pass strong{{color:var(--pass)}}
tr.sample-fail{{background:#fde8ec}}
tr.sample-fail td{{color:var(--fail)}}
code{{background:#eef2f6;padding:.1rem .35rem;border-radius:4px;font-size:.88em}}
.mini{{margin-top:.75rem;background:rgba(255,255,255,.65)}}
.muted{{color:var(--muted)}}
@media (max-width:700px){{.grid{{grid-template-columns:1fr}} dl{{grid-template-columns:1fr}}}}
</style></head><body><div class="wrap">
<div class="hero">
  <div class="verdict {verdict_class}">{verdict}</div>
  <p class="meta">Laudo ReqValLive · gerado {generated}</p>
  <p class="meta">Broker <code>{html.escape(session.mqtt_broker)}:{session.mqtt_port}</code>
     · tópico <code>{html.escape(session.mqtt_topic)}</code>
     · medição {started} → {ended}
     {"· <strong>ENCERRADA</strong>" if session.measurement_ended else ("· <strong>A MEDIR</strong>" if session.measuring else "")}</p>
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
  {note}
</div>

<div class="card">
  <h2>Resumo por requisito</h2>
  <table><thead><tr>
    <th>ID</th><th>Título</th><th>Métrica</th><th>Esperado</th><th>Resultado</th><th>Porquê</th>
  </tr></thead>
  <tbody>{''.join(summary_rows) or '<tr><td colspan=6>—</td></tr>'}</tbody></table>
</div>

{f'<div class="card"><h2>Evidência das falhas</h2>{"".join(fail_cards)}</div>' if fail_cards else ''}
{f'<div class="card"><h2>O que passou</h2>{"".join(pass_cards)}</div>' if pass_cards else ''}
{f'<div class="card"><h2>Pendentes</h2>{"".join(pending_cards)}</div>' if pending_cards else ''}

<div class="card">
  <h2>Definição dos requisitos</h2>
  <table><thead><tr><th>ID</th><th>Título</th><th>Texto</th><th>Critério</th></tr></thead>
  <tbody>{''.join(req_def_rows)}</tbody></table>
</div>

<div class="card">
  <h2>Últimas amostras MQTT</h2>
  <p class="muted">Linhas vermelhas = amostra que violou o limiar naquele instante.</p>
  <table><thead><tr>{''.join(f"<th>{h}</th>" for h in msg_headers)}</tr></thead>
  <tbody>{''.join(msg_rows) or '<tr><td colspan="' + str(len(msg_headers)) + '">—</td></tr>'}</tbody></table>
</div>
</div></body></html>"""
