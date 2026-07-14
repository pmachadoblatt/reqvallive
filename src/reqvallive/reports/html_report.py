"""Relatório HTML multi-drone."""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone

from reqvallive.models.session import MeasurementSession


def build_html_report(session: MeasurementSession) -> str:
    summary = session.summary()
    overall = summary.get("overall_ok")
    if overall is True:
        verdict, verdict_class = "PASS", "pass"
    elif overall is False:
        verdict, verdict_class = "FAIL", "fail"
    else:
        verdict, verdict_class = "N/A", "na"

    req_rows = []
    for req in session.requirements:
        sc = html.escape(req.success_criteria.model_dump_json())
        req_rows.append(
            f"<tr><td>{html.escape(req.req_id)}</td><td>{html.escape(req.title)}</td>"
            f"<td><code>{sc}</code></td></tr>"
        )

    drone_rows = []
    for d in session.drones.values():
        drone_rows.append(
            "<tr>"
            f"<td>{html.escape(d.id)}</td>"
            f"<td>{d.battery}</td>"
            f"<td>{d.latitude}</td>"
            f"<td>{d.longitude}</td>"
            f"<td>{html.escape(json.dumps(d.ok_by_req))}</td>"
            "</tr>"
        )

    msg_rows = []
    for m in session.message_log[-50:]:
        ts = datetime.fromtimestamp(m["ts"], tz=timezone.utc).strftime("%H:%M:%S")
        msg_rows.append(
            f"<tr><td>{ts}</td><td>{html.escape(str(m.get('drone')))}</td>"
            f"<td>{m.get('batteryLevel')}</td><td>{m.get('lat')}</td><td>{m.get('lon')}</td></tr>"
        )

    generated = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"/>
<title>Relatório ReqValLive</title>
<style>
body{{font-family:Segoe UI,sans-serif;margin:2rem;background:#f7f7f5;color:#1a1a1a}}
.card{{background:#fff;border:1px solid #ddd;padding:1.25rem;margin-bottom:1rem}}
.pass{{color:#0a7a2f}}.fail{{color:#b00020}}.na{{color:#666}}
.verdict{{font-size:1.75rem;font-weight:700}}
table{{width:100%;border-collapse:collapse;font-size:.9rem}}
th,td{{border-bottom:1px solid #eee;padding:.4rem .5rem;text-align:left}}
code{{background:#f0f0ee;padding:.1rem .3rem}}
</style></head><body>
<h1>Laudo de validação — ReqValLive</h1>
<p>Gerado em {generated}</p>
<div class="card"><div class="verdict {verdict_class}">{verdict}</div>
<p>Broker <code>{html.escape(session.mqtt_broker)}:{session.mqtt_port}</code> · tópico <code>{html.escape(session.mqtt_topic)}</code></p>
<ul>
<li>Drones: {summary.get("drone_count")}</li>
<li>Mensagens: {summary.get("message_count")}</li>
<li>Bateria min/max: {summary.get("min_battery")} / {summary.get("max_battery")}</li>
<li>Separação mín.: {summary.get("min_separation_m")}</li>
</ul></div>
<div class="card"><h2>Requisitos</h2>
<table><thead><tr><th>ID</th><th>Título</th><th>Critério</th></tr></thead>
<tbody>{''.join(req_rows) or '<tr><td colspan=3>—</td></tr>'}</tbody></table></div>
<div class="card"><h2>Drones</h2>
<table><thead><tr><th>ID</th><th>Bateria</th><th>Lat</th><th>Lon</th><th>OK/req</th></tr></thead>
<tbody>{''.join(drone_rows) or '<tr><td colspan=5>Nenhum drone</td></tr>'}</tbody></table></div>
<div class="card"><h2>Últimas mensagens</h2>
<table><thead><tr><th>Hora</th><th>Drone</th><th>Bat</th><th>Lat</th><th>Lon</th></tr></thead>
<tbody>{''.join(msg_rows) or '<tr><td colspan=5>—</td></tr>'}</tbody></table></div>
</body></html>"""
