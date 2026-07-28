#!/usr/bin/env python3
"""Exemplo de uso do SimReqValidator.

Demonstra:
1. Carregar requisitos de um arquivo JSON
2. Validar o schema e detectar vampiros
3. Exibir relatório de qualidade
4. Exportar JSON Schema canônico

Uso:
    python run_validation.py
"""

import json
from pathlib import Path

from simreqvalidator.schema import RequirementRecord, SchemaValidator


def main() -> None:
    """Executa exemplo de validação de requisitos."""

    # --- 1. Carregar requisitos ---
    examples_dir = Path(__file__).parent
    req_file = examples_dir / "requirements_example.json"

    print("=" * 60)
    print("SimReqValidator — Exemplo de Validação")
    print("=" * 60)
    print(f"\n📂 Carregando requisitos de: {req_file.name}")

    with open(req_file, encoding="utf-8") as f:
        data = json.load(f)

    requirements_data = data["requirements"]
    print(f"   → {len(requirements_data)} requisitos encontrados\n")

    # --- 2. Validar schema + detectar vampiros ---
    validator = SchemaValidator(strict_traceability=True)
    valid_requirements, report = validator.validate_batch(requirements_data)

    # --- 3. Exibir relatório ---
    print(report.summary)
    print()

    # Mostrar issues
    if report.issues:
        print("📋 Issues encontradas:")
        print("-" * 60)
        for issue in report.issues:
            print(f"  {issue.symbol} [{issue.code}] {issue.req_id}: {issue.message}")
            if issue.suggestion:
                print(f"     💡 Sugestão: {issue.suggestion}")
        print()

    # Mostrar vampiros
    vampires = [v for v in report.vampire_reports if v.is_vampire]
    if vampires:
        print(f"🧛 Requisitos Vampiros Detectados ({len(vampires)}):")
        print("-" * 60)
        for v in vampires:
            print(f"  {v.req_id} — Score: {v.quality_score}%")
            for reason in v.vampire_reasons:
                print(f"    • {reason}")
        print()

    # Mostrar DVM preview
    print("📊 Design Verification Matrix (Preview):")
    print("-" * 100)
    header = f"{'Req ID':<15} {'Título':<35} {'Nível':<12} {'Método':<12} {'Status':<8}"
    print(header)
    print("-" * 100)
    for req in valid_requirements:
        row = req.to_dvm_row()
        print(
            f"{row['req_id']:<15} "
            f"{row['title'][:33]:<35} "
            f"{row['level']:<12} "
            f"{row['vv_method']:<12} "
            f"{row['status_symbol']:<8}"
        )
    print()

    # --- 4. Exportar JSON Schema ---
    schema_file = examples_dir / "sim_req_schema.json"
    with open(schema_file, "w", encoding="utf-8") as f:
        f.write(RequirementRecord.model_json_schema(by_alias=True).__str__())
    print(f"📄 JSON Schema exportado para: {schema_file.name}")

    # --- 5. FASE B: Simular Validação Matemática (Evaluation Engine) ---
    print("\n" + "=" * 60)
    print("FASE B — Motor de Avaliação Matemática")
    print("=" * 60)
    
    from simreqvalidator.evaluators import EvaluationEngine
    
    # Criamos um log de simulação fake (ex: 2 drones se aproximando)
    fake_telemetry = [
        {"time": 0.0, "min_separation_m": 200.0, "geofence_active": 1.0},
        {"time": 1.0, "min_separation_m": 180.0, "geofence_active": 1.0},
        {"time": 2.0, "min_separation_m": 150.0, "geofence_active": 1.0},
        {"time": 3.0, "min_separation_m": 140.0, "geofence_active": 1.0}, # Violou a métrica de separação mínima (assumindo alvo >= 150)
        {"time": 4.0, "min_separation_m": 120.0, "geofence_active": 0.0}, # Violou geofence (assumindo alvo == True/1.0)
    ]
    
    print("📊 Log de Telemetria FAKE carregado (5 timesteps)")
    
    engine = EvaluationEngine()
    
    report_engine = engine.run(valid_requirements, fake_telemetry)
    
    print(f"\n🔍 Cobertura de Simulação: {'OK' if report_engine.coverage.is_covered else 'FALHOU'}")
    if not report_engine.coverage.is_covered:
        for issue in report_engine.coverage.issues:
            print(f"   ❌ {issue.message}")
            
    print(f"\n📈 Resultado Final da Validação: {'✅ PASS' if report_engine.passed_all else '❌ FAIL'}")
    print("-" * 60)
    for result in report_engine.evaluations:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        print(f"{status} | Requisito: {result.req_id}")
        print(f"       Detalhe: {result.details}")
        
    print("=" * 60)

    print("\n✅ Validação concluída com sucesso!")


if __name__ == "__main__":
    main()
