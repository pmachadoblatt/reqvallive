# Scripts auxiliares — ReqValLive

## `publish_three_drones.py` — telemetria MQTT de teste (casa / lab)

Publica **3 drones** simulados no broker MQTT, no mesmo formato do laboratório CONCEPTIO.

### Pré-requisitos

1. Venv do ReqValLive activo (`pip install -e .` já traz `paho-mqtt`)
2. Ficheiro `.env` na raiz do ReqValLive com:

```env
MQTT_BROKER=161.24.23.15
MQTT_PORT=1883
MQTT_USERNAME=marco
MQTT_PASSWORD=<senha do lab>
MQTT_TOPIC=conceptio/reqval
```

> A senha **não** vai no Git — só no teu `.env` local.

### Correr (casa)

Num terminal:

```powershell
cd ReqValLive
.\.venv\Scripts\Activate.ps1
python scripts/publish_three_drones.py
```

Noutro terminal:

```powershell
reqvallive
```

Na UI (http://127.0.0.1:8080):

1. Carrega requisitos (ex. `examples/battery_threshold.json` ou `examples/altitude_variation.json`)
2. Confirma gate **ACCEPT**
3. MQTT: mesmo broker/tópico do `.env` (`conceptio/reqval`)
4. **Conectar** → **Iniciar medição**
5. Deves ver alpha / bravo / charlie a entrar no feed
6. **Encerrar** → abrir relatório HTML

O subscriber escuta o tópico base **e** `tópico/#` (mensagens em `…/drone1`, etc.).

### Modos úteis

| Comando | Para testar |
|---------|-------------|
| `python scripts/publish_three_drones.py` | Bateria + altitude (default `both`) |
| `python scripts/publish_three_drones.py --mode battery` | Só `batteryLevel` (threshold) |
| `python scripts/publish_three_drones.py --mode altitude --altitude-span 2.5` | Variação AGL ~2.5 m → FAIL se `range <= 1` |
| `python scripts/publish_three_drones.py --mode altitude --altitude-span 0.5` | Variação pequena → PASS se `range <= 1` |
| `python scripts/publish_three_drones.py --broker 127.0.0.1 --topic home/reqval` | Broker local |

### Exemplo rápido — variação de altitude

1. Sessão com `examples/altitude_variation.json` (`range(altitudeAGL) <= 1`)
2. `python scripts/publish_three_drones.py --mode altitude --altitude-span 2.5`
3. Medir ~30–40 s → encerrar → relatório deve mostrar **FAIL** (peak-to-peak > 1 m)

---

## `probe_llm.py`

Utilitário antigo de descoberta de portas do Ollama. Preferir o botão **Testar LLM** na UI (`GET /api/llm/probe`).
