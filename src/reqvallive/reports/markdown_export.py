"""Exports Markdown do modelo gerado (requisitos + SysML)."""

from __future__ import annotations

from simreqvalidator.schema.requirement import RequirementRecord


def build_model_markdown(
    *,
    requirements: list[RequirementRecord],
    sysml_text: str,
    mqtt_topic: str,
    notes: str = "",
) -> str:
    lines = [
        "# Modelo ReqValLive",
        "",
        f"**Tópico MQTT:** `{mqtt_topic}`",
        "",
    ]
    if notes:
        lines.extend(["## Notas", "", notes, ""])

    lines.extend(["## Requisitos", ""])
    for req in requirements:
        sc = req.success_criteria.model_dump(mode="json")
        lines.extend(
            [
                f"### {req.req_id} — {req.title}",
                "",
                req.text,
                "",
                f"- **V&V:** `{req.vv_method}`",
                f"- **Critério:** `{sc}`",
                "",
            ]
        )

    lines.extend(
        [
            "## SysML V2 (textual)",
            "",
            "```sysml",
            sysml_text.strip(),
            "```",
            "",
        ]
    )
    return "\n".join(lines)
