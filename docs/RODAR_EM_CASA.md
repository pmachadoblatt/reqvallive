# Rodar o ReqValLive em casa (pull + setup)

Repositório único: **https://github.com/pmachadoblatt/reqvallive**  
(Não criar outro repo — o agente em casa faz `git pull` neste.)

## Layout obrigatório

```text
alguma-pasta/
├── reqvallive/              ← este repo (git clone / pull)
└── Sim_Req_Validator/       ← pasta IRMÃ (schema Vampire) — NÃO vem no git do reqvallive
```

Ver também: `DEPENDENCIA_SIM_REQ_VALIDATOR.md`.

O `Sim_Req_Validator` **não vai no git do reqvallive** — copie a pasta irmã do lab
(USB/OneDrive/outro). Depois rode `python scripts/ensure_simreq_range.py` para garantir
`Aggregation.RANGE` (necessário para SC de variação temporal).

## Setup (primeira vez)

```powershell
cd reqvallive
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python scripts/ensure_simreq_range.py
pip install -e ..\Sim_Req_Validator
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
python scripts/ensure_simreq_range.py
pip install -e ..\Sim_Req_Validator
pip install -e ".[dev]"
```

## Subir o app

```powershell
reqvallive
```

Abra http://127.0.0.1:8080 (hard refresh `Ctrl+F5` se a UI parecer antiga).

## Fluxo CATIA → GSE → MQTT → UPDATE

1. Aba **Export CATIA** → Carregar exemplo → **Validar export (OK/NOK)**
2. **Montar GSE** → Continuar MQTT
3. Terminal 2: `python scripts/publish_three_drones.py`
4. Conectar → Iniciar medição → Encerrar
5. **UPDATE CATIA (LLM)** → Baixar `verification_update.json`
   - Sem Ollama: o `stop` já gera o UPDATE determinístico; o botão tenta enriquecer com LLM

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
