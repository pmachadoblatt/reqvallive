# ReqValLive

Validação de requisitos em tempo real via **MQTT multi-drone**, geração de **SysML V2** (diagrama visual + textual) e relatório HTML.

Entrada preferencial (tese / Christopher): **export CATIA SysML** com `_go_to_verification` → gate OK/NOK → Montar GSE → medir MQTT → **UPDATE CATIA** (LLM opcional). Markdown+LLM continua disponível como caminho secundário.

> **⚠️ Dependência externa obrigatória:** o pacote **`Sim_Req_Validator`** (`simreqvalidator`) **não está neste repositório**. Sem a pasta irmã `../Sim_Req_Validator` e `pip install -e ../Sim_Req_Validator`, a app **não funciona**.  
> Ver: [`DEPENDENCIA_SIM_REQ_VALIDATOR.md`](DEPENDENCIA_SIM_REQ_VALIDATOR.md) · setup em casa: [`docs/RODAR_EM_CASA.md`](docs/RODAR_EM_CASA.md)

## Fluxo

1. **Export CATIA** (`.sysml`) → Validar OK/NOK → **Montar GSE**
2. MQTT → Iniciar medição → Encerrar → **UPDATE CATIA (LLM)** / baixar JSON
3. Alternativa: Markdown → Interpretar com LLM → diagrama + `.sysml`
4. Relatório HTML de procedimento V&V

## Instalação

**Antes de tudo:** garanta `Dissertacao/Sim_Req_Validator` ao lado de `Dissertacao/reqvallive` (ver aviso acima).

```powershell
cd ReqValLive
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ..\Sim_Req_Validator   # OBRIGATÓRIO — schema Vampire
pip install -e ".[dev]"
copy .env.example .env
# Editar .env: MQTT_PASSWORD, LLM_API_KEY, LLM_BASE_URL se necessário
```

## Executar

```powershell
reqvallive
```

http://127.0.0.1:8080

## Configuração LLM

No `.env` (nunca commitar a chave):

```
LLM_BASE_URL=https://ollama.conceptio.com.br/v1
LLM_API_KEY=<token>
LLM_MODEL=qwen3.6:35b
```

Na UI: botão **Testar LLM** → `GET /api/llm/probe`.

## Payload do laboratório

Cada mensagem identifica um drone (`droneName`). Exemplos de campos usados:

- `batteryLevel` / `remainingCharge`
- `location.latitude` / `longitude` / `altitude`
- `altitudeAGL`
- Agregação: `min_separation_m` calculada entre todos os drones activos

## Testar em casa (MQTT simulado)

Guia completo: [`docs/RODAR_EM_CASA.md`](docs/RODAR_EM_CASA.md).

Para não depender dos drones reais, publica 3 drones simulados:

```powershell
# Terminal 1 — app
reqvallive

# Terminal 2 — telemetria
python scripts/publish_three_drones.py
```

Credenciais MQTT e LLM vêm do `.env` (`MQTT_PASSWORD`, `LLM_API_KEY`, etc.).

Fluxo CATIA (sem Magic aberto): exemplo `.sysml` → Validar OK/NOK → Montar GSE → MQTT → Encerrar → **UPDATE CATIA (LLM)**.

Modos úteis do publisher:

```powershell
python scripts/publish_three_drones.py --mode battery
python scripts/publish_three_drones.py --mode altitude --altitude-span 2.5
```

Na UI use o mesmo broker/tópico do `.env` (ex.: `conceptio/reqval`). O app escuta também `tópico/#`.

## Segurança

Não compartilhe tokens de LLM nem senhas MQTT em chats públicos; rode a rotação da chave se foi exposta.
Credenciais ficam só no `.env` (gitignored).
