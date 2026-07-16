# Banco de ideias — requisitos para testar com o LLM

Use um destes blocos (ou combine) na entrada Markdown do ReqValLive.
Métricas alinhadas ao payload MQTT do lab (`dji_mini_4_pro`, etc.).

---

## Suite 1 — Bateria e energia

### RQ-BAT-001
Cada drone deve manter `batteryLevel >= 20` (%).

### RQ-BAT-002
`remainingCharge >= batteryNeededToGoHome + 5` (margem para RTL).

### RQ-BAT-003
Se `isFlying == true`, então `remainingFlightTime >= timeNeededToGoHome + timeNeededToLand`.

---

## Suite 2 — Separação e posição

### RQ-SEP-001
Separação mínima entre quaisquer dois drones: `min_separation_m >= 20` (metros).

### RQ-POS-001
`distanceToHome <= maxRadiusCanFlyAndGoHome` (metros).

### RQ-ALT-001
Altitude AGL em envelope seguro: `altitudeAGL` entre 5 e 120 metros (range).

### RQ-ALT-VAR-001
Altitude não deve **variar** mais de 1 m na janela de medição:
`statistical` + `aggregation=range` + `metric=altitudeAGL` + `operator=<=` + `value=1`
(sem inventar métrica `altitude_variation` — o agregado é sobre o campo MQTT).

### RQ-BAT-VAR-001
`batteryLevel` não deve variar mais de 5% na janela (`range(batteryLevel) <= 5`).

---

## Suite 3 — Navegação / missão

### RQ-NAV-001
Com missão activa (`waypointMission.state == EXECUTING`), `satelliteCount >= 10`.

### RQ-NAV-002
`fcConnected == true` durante todo o voo (`isFlying`).

### RQ-NAV-003
Velocidade horizontal limitada: `speed.horizontal <= 12` (m/s) — métrica `speed_horizontal`.

---

## Suite 4 — Segurança operacional

### RQ-SAFE-001
Nunca entrar em bateria crítica: `batteryLevel > seriousLowBatteryThreshold`.

### RQ-SAFE-002
Com `isFlying`, `homeSet == true`.

### RQ-SAFE-003
`isManualOverrideActive == false` durante missão automática waypoint.

---

## Como pedir ao LLM (texto sugerido)

```markdown
# Requisitos missão Spectio / UTM

Telemetria MQTT por drone (campos: batteryLevel, location.lat/lon,
altitudeAGL, distanceToHome, speed.horizontal, satelliteCount,
remainingFlightTime, timeNeededToGoHome, timeNeededToLand,
batteryNeededToGoHome, isFlying, homeSet, fcConnected).

## RQ-BAT-001 — Bateria mínima por drone
Cada aeronave deve manter batteryLevel >= 20 percent (all entities).

## RQ-SEP-001 — Separação mínima
Distância Haversine mínima entre drones >= 20 meters (métrica min_separation_m).

## RQ-ALT-001 — Envelope AGL
altitudeAGL deve permanecer entre 5 e 120 meters.

## RQ-NAV-001 — GNSS mínimo
satelliteCount >= 10 enquanto isFlying.

Gere success_criteria threshold/range com metric igual ao nome do campo MQTT.
```

---

## Notas de medição actual no ReqValLive

| Métrica | Fonte |
|---------|--------|
| `batteryLevel` | por drone |
| `altitudeAGL`, `distanceToHome`, `speed_horizontal` | por drone (campo/path; `location.altitude` → altitudeAGL) |
| `min_separation_m` | calculada entre todos os drones com `location` |
| `statistical` `range`/`max`/`min` | agregado na **janela de medição** sobre a métrica MQTT acima (peak-to-peak, etc.) |
| boolean / temporal / mean·percentile | ainda não no motor live |
