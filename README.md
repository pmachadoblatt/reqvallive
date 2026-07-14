# ReqValLive

Validação de requisitos em tempo real via **MQTT embutido**, com geração de **SysML V2 textual**, diagrama na UI e **relatório HTML** ao encerrar.

Não depende do CATIA Magic para medir. O `.sysml` gerado serve de referência textual (colar no Textual Editor).

## Fluxo

1. Colar / carregar JSON de requisito (`RequirementRecord`)
2. Validar (schema + Vampire Detector do `Sim_Req_Validator`)
3. Gerar modelo SysML + configurar broker/tópico
4. **Iniciar medição** → subscriber MQTT avalia OK/NOK em tempo real
5. **Encerrar medição** → abrir relatório HTML

## Requisitos

- Python 3.11+
- Pacote irmão [`../Sim_Req_Validator`](../Sim_Req_Validator) (path dependency)
- Broker MQTT acessível (lab ou Mosquitto local)
- Publisher (ex.: `Dissertação/simulator/battery_publisher.py`)

## Instalação rápida

```powershell
cd C:\Users\CONCEPTIO\Desktop\Pedro\Conceptio\UTM\Antigravity\ReqValLive
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ..\Sim_Req_Validator
pip install -e ".[dev]"
copy .env.example .env
```

## Executar

```powershell
reqvallive
# ou
python -m reqvallive.main
```

Abra http://127.0.0.1:8080

### Lab / simulador

Com o simulador da dissertação a publicar em `conceptio/reqval`:

```powershell
cd ..\Dissertação\simulator
# com broker local ou do lab configurado em MQTT_*
python battery_publisher.py
```

Ou use o broker do lab no `.env` / formulário da UI (`MQTT_BROKER`, `MQTT_USERNAME`, `MQTT_PASSWORD`, `MQTT_TOPIC`).

## Envelope MQTT

**Campo directo** (genérico): o nome da métrica no JSON do requisito deve existir no payload:

```json
{ "battery_level": 85.0, "timestamp": 1710000000 }
```

**Distância / separação** (`min_separation_m`, `collision_distance`, …):

```json
{
  "entities": [
    { "id": "drone-a", "latitude": -30.0, "longitude": -51.2 },
    { "id": "drone-b", "latitude": -30.0002, "longitude": -51.2002 }
  ],
  "timestamp": 1710000000
}
```

Ou valor pré-calculado: `{ "min_separation_m": 25.4, ... }`.

MVP live: `threshold` / `range` sobre qualquer métrica fornecível pelo payload.

Exemplos: [`examples/battery_threshold.json`](examples/battery_threshold.json), [`examples/min_separation.json`](examples/min_separation.json).

## API

| Método | Rota | Função |
|--------|------|--------|
| POST | `/api/requirements/validate` | Validar JSON |
| POST | `/api/sessions` | Criar sessão + SysML |
| POST | `/api/sessions/{id}/start` | Iniciar MQTT |
| POST | `/api/sessions/{id}/stop` | Encerrar |
| GET | `/api/sessions/{id}/sysml` | Download `.sysml` |
| GET | `/api/sessions/{id}/report` | Relatório HTML |
| GET | `/api/sessions/{id}/stream` | SSE tempo real |

## Testes

```powershell
pytest
```

## Relação com o mestrado

- Schema canónico: `Sim_Req_Validator`
- Exploração CATIA / limitação Simulation: `Dissertação` (branch `feature/evaluation-mqtt`)
- Esta ferramenta é o caminho plug-and-play para demo de validação durante experimento
