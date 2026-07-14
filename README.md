# ReqValLive

Validação de requisitos em tempo real via **MQTT multi-drone**, geração de **SysML V2** (diagrama visual + textual) e relatório HTML. Entrada preferencial: **Markdown** interpretado por **LLM local** (Qwen no lab).

## Fluxo

1. Colar / carregar `.md` de requisitos → **Interpretar com LLM**
2. Ver diagrama estilo Magic + baixar `.sysml` e modelo `.md`
3. Configurar MQTT (IP do lab por defeito) → **Conectar**
4. **Iniciar monitoramento** → modelo ao vivo + status MQTT + mensagens + medição multi-drone

## Instalação

```powershell
cd ReqValLive
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ..\Sim_Req_Validator
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
- `location.latitude` / `longitude`
- Agregação: `min_separation_m` calculada entre todos os drones activos

## Segurança

Não partilhe tokens de LLM em chats públicos; rode a rotação da chave se foi exposta.
