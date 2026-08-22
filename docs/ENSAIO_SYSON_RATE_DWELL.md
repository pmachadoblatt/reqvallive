# Ensaio SysON — rate e dwell (Jefferson)

**Data:** 2026-08-22  
**Objetivo:** corrida documentada para o capítulo IV (Resultados) com os critérios `rate` e `dwell` do demo SysON.  
**Artefactos:** `models/syson/reqvallive_demo.sysml`, `scripts/publish_three_drones.py`, laudo HTML ReqValLive.

---

## Pré-requisitos

| Item | Valor |
|------|--------|
| ReqValLive | `uvicorn reqvallive.main:app --reload` (ou equivalente) |
| Broker MQTT | `.env`: `MQTT_BROKER`, `MQTT_PORT`, `MQTT_USERNAME`, `MQTT_PASSWORD`, `MQTT_TOPIC` |
| Simulador | `python scripts/publish_three_drones.py --mode battery --interval 1.0` |
| Modelo SysON | Importar projeto com `reqvallive_demo.sysml` ou usar SysON live |

**Requisitos foco deste ensaio:**

| ID | Tipo SC | Critério | Veredicto esperado (simulador default) |
|----|---------|----------|----------------------------------------|
| `RQ_BAT_RATE_001` | `rate` | `\|d(batteryLevel)/dt\| ≤ 30 %/min` | **FAIL** (~60 %/min a 1 Hz, Δ=1 %/s) |
| `RQ_BAT_DWELL_001` | `dwell` | `batteryLevel < 20` por ≤ 2 s | **FAIL** (charlie inicia a 15%) |

Outros requisitos do demo (`threshold`, `range`, `statistical`, separação) podem correr na mesma sessão; registar PASS/FAIL na tabela final.

---

## Protocolo (passo a passo)

### 1. Preparar telemetria

```powershell
cd C:\Users\CONCEPTIO\Desktop\Pedro\Conceptio\UTM\Antigravity\ReqValLive
python scripts/publish_three_drones.py --mode battery --interval 1.0
```

- **alpha:** bateria 100 → desce 1 %/s (taxa ~60 %/min)  
- **charlie:** bateria 15 % (abaixo de 20 % desde t=0)  
- Tópicos: `<MQTT_TOPIC>/drone1`, `drone2`, `drone3`

### 2. Importar SysON

1. UI → **Connect / list projects** → **Import from SysON**  
2. Confirmar gate **ACCEPT** para requisitos com SC no modelo  
3. **Mount GSE** → **Continue to MQTT**

### 3. MQTT e medição

1. Broker/topic iguais ao simulador (wildcard `#` no subscriber)  
2. **Connect** → **Start measurement** (congela `approved_sc_snapshot`)  
3. Deixar correr **≥ 30 s** (garantir amostras para rate e dwell)  
4. **Stop measurement** → abrir **HTML report**

### 4. Publicar no SysON (opcional)

**Publish to SysON** → verificar `VerificationResult_*` ligado a cada requisito.

---

## Evidência a capturar (cap. IV)

| # | Captura | Ficheiro sugerido |
|---|---------|-------------------|
| 1 | Explorador SysON com `RQ_BAT_RATE_001` / `RQ_BAT_DWELL_001` + SC | `fig_syson_rate_dwell.png` |
| 2 | UI live — veredicto FAIL latched | `fig_ui_live_fail.png` |
| 3 | Laudo HTML — secções 1–3 (método Test, topic, snapshot) | `fig_laudo_procedimento.png` |
| 4 | Laudo HTML — resultados rate/dwell | `fig_laudo_rate_dwell.png` |
| 5 | SysON após publish — `VerificationResult` | `fig_syson_verification.png` |

---

## Tabela de resultados (preencher após corrida)

| Requisito | Tipo SC | Gate | Veredicto live | Notas |
|-----------|---------|------|----------------|-------|
| `RQ_BAT_RATE_001` | rate | ACCEPT | FAIL (esperado) | 1ª violação em alpha; taxa ~60 %/min |
| `RQ_BAT_DWELL_001` | dwell | ACCEPT | FAIL (esperado) | charlie < 20 % > 2 s |
| `RQ_BAT_001` | threshold | ACCEPT | PASS/FAIL | conforme corrida |
| `RQ_SEP_001` | threshold (global) | ACCEPT | PASS | separação Haversine |
| … | … | … | … | … |

---

## Validação automática (regressão)

```powershell
pytest tests/test_jefferson_natures.py tests/test_procedure_report.py tests/test_sc_snapshot.py -q
```

113+ testes cobrem motor `rate`/`dwell`, snapshot congelado e secções do laudo.

---

## Ameaças à validade (ensaio)

- **Simulador local**, não voo real — aceitável para PoC; lab real já demonstrado em 2026-08.  
- **Taxa derivada** depende do intervalo de publicação (1 Hz no script).  
- **Dwell** mede persistência contínua da condição `< 20 %`, não eventos discretos.

---

## Referências

- `docs/JEFFERSON_NATUREZAS_OBSERVACAO.md`  
- `docs/SYSON_CONTRATO_DOC.md`  
- `models/syson/reqvallive_demo.sysml`
