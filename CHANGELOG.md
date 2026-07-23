# Changelog

Todas as mudanças notáveis do **ReqValLive** são registadas neste ficheiro.

O formato inspira-se em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).
Datas no formato `AAAA-MM-DD`.

---

## [Unreleased]

### Added (2026-07-23)

- Entrada **Export CATIA (.sysml)** na UI web (assistente): carregar exemplo, upload, validar OK/NOK
- Skill `ui-ux-pro-max` instalada em `.cursor/skills/` (e `~/.cursor/skills/`)
- Teste ponta a ponta do passo 1: `tests/test_step1_catia_flow.py`
- **Montar GSE** (`POST .../gse/mount`) + `validation_status.json` + UI no passo 2
- **UPDATE CATIA pós-medição**: ao encerrar, gera `verification_update.json`; botão enriquece com Ollama/LLM
- Guia `docs/RODAR_EM_CASA.md` para pull/setup em casa
- `scripts/ensure_simreq_range.py` + patch `Aggregation.RANGE` para a pasta irmã `Sim_Req_Validator`

### Added (2026-07-22)

- Relatório HTML reestruturado como **procedimento de V&V** (P0 1.2):
  1. método + gate ACCEPT/REJECT por requisito  
  2. condições de medição (MQTT broker/tópico, janela start/end, duração, drones)  
  3. snapshot do SC aprovado  
  4. esperado × observado com evidência  
  5. amostras MQTT  
- Teste `tests/test_procedure_report.py`
- Script `scripts/publish_three_drones.py` reforçado para teste em casa (`.env`, modos battery/altitude, CLI)
- Guia `scripts/README.md` + secção no README principal
- Subscriber MQTT passa a escutar também `tópico/#` (mensagens `…/drone1`, etc.)

### Security (2026-07-22)

- Removida senha MQTT hardcoded do publisher; usa `MQTT_PASSWORD` / `--password`
- `scripts/probe_llm.py` deixa de embutir API key (lê `.env`)

### Added (2026-07-16)

- Suporte genérico a critérios `statistical` live com `aggregation = range|max|min` sobre a **mesma métrica MQTT** já existente
- Caso de uso de variação temporal: `range(metric) <= X` para requisitos como “não variar mais de X” sem criar métricas artificiais
- Exemplo `examples/altitude_variation.json`
- Testes `tests/test_window_variation.py` para variação de altitude e bateria com o mesmo mecanismo
- Testes `tests/test_sc_snapshot.py` para o freeze do SC aprovado no instante do `start`
- Endpoint `GET /api/sessions/{id}/approved-sc` para consultar o snapshot imutável da corrida
- Nova secção no relatório HTML: **Success Criteria aprovado (snapshot)**
- Documento `docs/ROTEIRO_IMPLEMENTACAO.md` com plano P0/P1 da PoC

### Changed (2026-07-16)

- `location.altitude` passa a servir como fallback para `altitudeAGL`
- Prompt/normalização do LLM passam a mapear requisitos de variação para `success_criteria.type = statistical` com `aggregation = range`
- Gate ACCEPT/REJECT agora aceita `statistical` com `range|max|min` no live MQTT
- Ao iniciar a medição (`/start`), a sessão congela uma cópia do requisito + SC + gate em `approved_sc_snapshot`
- A avaliação live, a API pública e o relatório passam a usar a cópia aprovada da corrida, não apenas o requisito editável
- `docs/FEATURES_MESTRADO_SE.md` e `docs/ROTEIRO_IMPLEMENTACAO.md` atualizados para refletir o novo motor temporal e a conclusão do item 1.1

### Added (2026-07-15)

- Motor `eval/criteria_gate.py`: gate ACCEPT/REJECT de Success Criteria (SIS-08 Methods / MSFC-3173)
- Bloqueio de `/connect` e `/start` com HTTP 409 se gate ≠ ACCEPT
- `GET /api/criteria/model` + modelo pedagógico na página inicial (modal) + `GET /api/criteria/example.md`
- `POST /sessions/{id}/criteria/evaluate` para reavaliar
- Testes `tests/test_criteria_gate.py` e `examples/success_criteria_model.md`
- **Fix:** veredicto live **latcheia FAIL** se qualquer amostra violar o limiar (`all_timesteps`); já não usa só o último valor (caso charlie 15%→25% com relatório PASS errado)
- Relatório e medição ao vivo mostram **atual + mínimo + 1ª violação + #falhas/amostras** (sem confundir o valor «travado» com o presente)
- UI de medição: faixa PASS/FAIL, cartões por drone, feed com violações, gráfico atual vs mínimo
- Home simplificada + modal «Como deve ser o critério?» + download do exemplo
- Material SIS-08 Methods em `docs/` e exemplos de laudos PASS/FAIL

_Próximas iterações (backlog)_

- Passo UI dedicado «Critério de validação» (painel completo errors/warnings/sugestões)
- Critérios live booleanos / temporais (além de `threshold` e `range`)
- Enricher de diagrama (PlantUML/Kroki) se Mermaid não bastar
- Parser livre de PDF/Word além de Markdown + LLM
- Secção do gate no relatório HTML

---

## [2026-07-14] — Fluxo LLM, diagrama, multi-drone e robustez

Dia de consolidação do produto standalone (pivô face ao limite da simulação CATIA Magic): entrada por Markdown, interpretação com LLM do lab, modelo visual, MQTT multi-drone e relatório utilizável.

### Added

- Fluxo UI em passos: Markdown → interpretar com LLM → modelo SysML/diagrama → MQTT → monitorização → relatório HTML
- Cliente LLM OpenAI-compatible (Ollama Conceptio em `ollama.conceptio.com.br`) com probe `/api/llm/probe`
- Diagrama visual estilo Magic + vista UML Mermaid (`diagram.js`)
- Export de `.sysml` e modelo `.md` por sessão
- Monitor multi-drone: bateria, posição, `min_separation_m` (Haversine), feed MQTT e gráfico live
- Suite de ideias de requisitos em `examples/llm_test_ideas.md`
- Script auxiliar `scripts/publish_three_drones.py` para telemetria de teste
- Normalização robusta da saída do LLM (enums `priority`/`level`/`vv_method`, critérios)
- Congelamento explícito ao **Encerrar medição** (`measurement_ended`) — resultados deixam de ser alterados por MQTT
- Relatório HTML redesenhado: PASS/FAIL, contadores, “esperado vs observado”, secção “O que falhou” e porquê

### Changed

- UI e gráfico passam a mostrar só as **métricas pedidas pelos requisitos** (já não forçam barra de bateria)
- Prompt do LLM: não inventar requisitos (ex. bateria) que o Markdown não peça
- Erros LLM/schema devolvem JSON (`502`/`422`) em vez de 500 texto (`Internal Server Error`)
- Defaults MQTT/LLM alinhados ao lab Conceptio

### Fixed

- Crash da UI por `addEventListener` em elementos em falta (listeners defensivos + bind no `DOMContentLoaded`)
- URL errada do Ollama (`:11434`) → `https://ollama.conceptio.com.br/v1`
- `SyntaxError: Unexpected token 'I'` no browser ao interpretar Markdown (resposta 500 não-JSON + `priority` inválido do modelo)
- “Encerrar medição” que parecia continuar a medir (avaliação/ingest sem freeze)
- Diagrama/feed/gráfico always-on de bateria mesmo em testes só de distância

### Commits do dia (histórico git)

| Commit | Resumo |
|--------|--------|
| `ae3594c` | Diagrama SysML estilo CATIA e métricas genéricas (distância) |
| `d440d5c` | Fluxo Markdown+LLM, diagrama visual Magic e monitor multi-drone |
| `811c65c` | Fix UI listeners, URL Ollama, probe LLM |
| `26f8481` | Mermaid UML + ideias de requisitos para o LLM |
| _(este commit)_ | Freeze da medição, métricas só do MD, relatório claro, changelog |

---

## [2026-07-13] — Bootstrap do ReqValLive

Criação do repositório MVP independente do CATIA Magic para validar requisitos contra telemetria MQTT real.

### Added

- App FastAPI + UI web embutida (`reqvallive`)
- Subscriber MQTT (Paho) por sessão
- Avaliação live `threshold` / `range` via schema `Sim_Req_Validator` (Vampire)
- Geração textual SysML v2 e relatório HTML inicial
- Exemplos JSON (`battery_threshold`) e payload MQTT
- Testes MVP sem broker/LLM real
- Repo público: https://github.com/pmachadoblatt/reqvallive

### Context

Pivô a partir da exploração CATIA Magic 2026x / SysML v2 Simulation (branch de dissertação): macros actualizam o modelo KerML estático, mas o runtime de simulação (`:=`) não reflecte telemetria live — daí a ferramenta standalone.

---

## Notas de execução (lab)

```text
MQTT: 161.24.23.15 · user marco · topic conceptio/reqval
LLM:  https://ollama.conceptio.com.br/v1 · modelo qwen3.6:35b
UI:   http://127.0.0.1:8080  (após `reqvallive`)
```

Credenciais e `LLM_API_KEY` ficam apenas em `.env` local (gitignored).
