# Rodar o ReqValLive em casa (pull + setup)

Repositório único: **https://github.com/pmachadoblatt/reqvallive**

O app completo (código + schema `simreqvalidator`) vai **neste** repositório:
`vendor/Sim_Req_Validator/`. Um `git clone` / `git pull` basta — não precisa de pasta irmã.

## Primeira vez (ou máquina nova)

```powershell
git clone https://github.com/pmachadoblatt/reqvallive.git
cd reqvallive
.\scripts\bootstrap.ps1
```

Ou manualmente:

```powershell
cd reqvallive
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .\vendor\Sim_Req_Validator
pip install -e ".[dev]"
copy .env.example .env
```

Edite `.env` (não vai para o Git):

```env
MQTT_BROKER=161.24.23.15
MQTT_PORT=1883
MQTT_USERNAME=marco
MQTT_PASSWORD=<senha do lab>
MQTT_TOPIC=conceptio/reqval

LLM_BASE_URL=https://ollama.conceptio.com.br/v1
LLM_API_KEY=<sua chave>
LLM_MODEL=qwen3.6:35b
```

## Atualizar depois de um push do trabalho

```powershell
cd reqvallive
git pull origin master
.\.venv\Scripts\Activate.ps1
pip install -e .\vendor\Sim_Req_Validator
pip install -e ".[dev]"
```

## Subir SysON + app (fluxo principal em casa)

O anfitrião do modelo é o **SysON local** (Docker). Não precisa de TWC/VPN para continuar.

```powershell
# 1) SysON (primeira vez descarrega imagens — alguns minutos)
.\deploy\syson\up.ps1
# → http://localhost:8081

# 2) App
.\.venv\Scripts\Activate.ps1
reqvallive
# → http://127.0.0.1:8080  (Ctrl+F5 se a UI parecer antiga)
```

No SysON: criar projeto (ex. `ReqTest`) → importar/colar `models/syson/reqvallive_demo.sysml`
(ou criar `RQ_01` + atributos SC + `_go_to_verification`). Contrato: `docs/SYSON_CONTRATO_DOC.md`.

No ReqValLive: separador **SysON** → Probe → Import `RQ_01` → medir → **Publicar no SysON**.
Aparece sob o requisito um item `VerificationResult_FAIL_…` (ou PASS) com Documentation + atributos.

Detalhe Docker / backup Postgres: `deploy/syson/README.md`.

## Fluxo legado CATIA → GSE → MQTT → UPDATE

1. Aba **Export CATIA** → Carregar exemplo → **Validar export (OK/NOK)**
2. **Montar GSE** → Continuar MQTT
3. Terminal 2: `python scripts/publish_three_drones.py`
4. Conectar → Iniciar medição → Encerrar
5. **UPDATE CATIA (LLM)** → baixar artefactos Magic (secundário ao fecho SysON):
   - JSON + `.sysml` arquivo (import `.sysml` ≠ sync do aberto; ver `docs/CATIA_UPDATE_FORMATOS.md`)
   - CSV Sync só se o Magic v1/tabular o permitir — **não** é o caminho garantido no SysML v2

## Testes rápidos

```powershell
python -m pytest tests/test_import_catia.py tests/test_step1_catia_flow.py tests/test_gse_mount.py tests/test_catia_update.py -q
```

## O que o agente em casa deve saber

- Entrada principal: `.sysml` com `doc /* _go_to_verification */` + SC estruturado
- Gate OK/NOK = checklist Methods/MSFC (sem LLM)
- GSE = config de medição (`gse_config.json`), não o laudo final
- Laudo = relatório HTML
- UPDATE CATIA = JSON com tags `_verification_PASS` / `_FAIL` + texto para o `doc` no Magic
- LLM (Ollama) = Markdown opcional + enriquecimento do UPDATE pós-medição
- Schema Vampire: `vendor/Sim_Req_Validator` (já no git)
- **Amanhã no trabalho:** lembrete TWC/REST — `docs/LEMBRETE_TWC_REST_EVOLUCAO.md`
  (Collaborate do lab = caminho para evoluir UPDATE via REST; não pivote o MVP)
