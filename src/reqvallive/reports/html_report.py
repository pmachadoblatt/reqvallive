"""Relatório HTML estilo laudo de teste."""

from __future__ import annotations

import html
from datetime import datetime, timezone

from reqvallive.models.session import MeasurementSession


def build_html_report(session: MeasurementSession) -> str:
    summary = session.summary()
    sc = session.requirement.success_criteria
    criteria = html.escape(sc.model_dump_json())
    final = summary.get("final_pass")
    if final is True:
        verdict = "PASS"
        verdict_class = "pass"
    elif final is False:
        verdict = "FAIL"
        verdict_class = "fail"
    else:
        verdict = "N/A"
        verdict_class = "na"

    rows = []
    for s in session.samples[-100:]:
        ts = datetime.fromtimestamp(s.timestamp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        status = "OK" if s.ok else "NOK"
        rows.append(
            f"<tr class=\"{'ok' if s.ok else 'nok'}\">"
            f"<td>{ts}</td><td>{s.value}</td><td>{status}</td>"
            f"<td>{html.escape(s.detail)}</td></tr>"
        )
    table_body = "\n".join(rows) or "<tr><td colspan='4'>Sem amostras</td></tr>"

    chart_labels = [str(round(s.timestamp, 1)) for s in session.samples[-200:]]
    chart_values = [s.value for s in session.samples[-200:]]

    generated = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8"/>
  <title>Relatório ReqValLive — {html.escape(session.requirement.req_id)}</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <style>
    body {{ font-family: "Segoe UI", system-ui, sans-serif; margin: 2rem; color: #1a1a1a; background: #f7f7f5; }}
    h1 {{ font-size: 1.5rem; margin-bottom: 0.25rem; }}
    .meta {{ color: #555; margin-bottom: 1.5rem; }}
    .card {{ background: #fff; border: 1px solid #ddd; padding: 1.25rem; margin-bottom: 1rem; }}
    .verdict {{ font-size: 1.75rem; font-weight: 700; }}
    .pass {{ color: #0a7a2f; }}
    .fail {{ color: #b00020; }}
    .na {{ color: #666; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
    th, td {{ border-bottom: 1px solid #eee; padding: 0.4rem 0.5rem; text-align: left; }}
    tr.nok td {{ background: #fff0f0; }}
    code {{ background: #f0f0ee; padding: 0.1rem 0.3rem; }}
  </style>
</head>
<body>
  <h1>Laudo de validação — ReqValLive</h1>
  <p class="meta">Gerado em {generated}</p>

  <div class="card">
    <div class="verdict {verdict_class}">{verdict}</div>
    <p><strong>Requisito:</strong> {html.escape(session.requirement.req_id)} — {html.escape(session.requirement.title)}</p>
    <p>{html.escape(session.requirement.text)}</p>
    <p><strong>Critério:</strong> <code>{criteria}</code></p>
  </div>

  <div class="card">
    <h2>MQTT</h2>
    <p>Broker: <code>{html.escape(session.mqtt_broker)}:{session.mqtt_port}</code></p>
    <p>Tópico: <code>{html.escape(session.mqtt_topic)}</code></p>
  </div>

  <div class="card">
    <h2>Resumo</h2>
    <ul>
      <li>Amostras: {summary.get("sample_count")}</li>
      <li>Violações: {summary.get("violations")}</li>
      <li>Mínimo: {summary.get("min")}</li>
      <li>Máximo: {summary.get("max")}</li>
      <li>Último: {summary.get("last")}</li>
    </ul>
    <canvas id="chart" height="100"></canvas>
  </div>

  <div class="card">
    <h2>Amostras (últimas 100)</h2>
    <table>
      <thead><tr><th>Timestamp</th><th>Valor</th><th>Status</th><th>Detalhe</th></tr></thead>
      <tbody>
        {table_body}
      </tbody>
    </table>
  </div>

  <script>
    const labels = {chart_labels};
    const values = {chart_values};
    if (values.length) {{
      new Chart(document.getElementById('chart'), {{
        type: 'line',
        data: {{
          labels,
          datasets: [{{
            label: '{html.escape(session.requirement.success_criteria.metric)}',
            data: values,
            borderColor: '#1f4e79',
            tension: 0.2,
            pointRadius: 0
          }}]
        }},
        options: {{
          plugins: {{ legend: {{ display: true }} }},
          scales: {{ x: {{ display: false }} }}
        }}
      }});
    }}
  </script>
</body>
</html>
"""
