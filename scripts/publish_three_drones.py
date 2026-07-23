"""Publica telemetria simulada de 3 drones no MQTT para testar o ReqValLive em casa.

Lê credenciais do ambiente / `.env` (nunca hardcode a senha).

Uso típico (a partir da pasta ReqValLive, com venv activo):

    python scripts/publish_three_drones.py
    python scripts/publish_three_drones.py --mode altitude --altitude-span 2.5
    python scripts/publish_three_drones.py --broker 127.0.0.1 --topic home/reqval

Modos:
  battery   — bateria sobe/desce (bom para threshold de batteryLevel)
  altitude  — altitude AGL oscila (bom para statistical range / «não variar»)
  both      — os dois ao mesmo tempo (default)

Ctrl+C para parar.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import time
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from paho.mqtt import client as mqtt

# ---------------------------------------------------------------------------
# Defaults de geometria / dinâmica (não são segredos)
# ---------------------------------------------------------------------------

CENTER_LAT = -23.189612
CENTER_LON = -45.884123
CENTER_ALT = 612.4
HOME_LAT = -23.189600
HOME_LON = -45.884100

RADIUS_M = 60.0
ORBIT_OMEGA = 2 * math.pi / 90.0  # 1 volta a cada 90 s
METERS_PER_DEG_LAT = 111_320.0

BATTERY_MIN = 15
BATTERY_MAX = 100
BASE_AGL = 24.5

BASE_PAYLOAD = {
    "droneModel": "Mini4Pro",
    "speed": {"x": 0.0, "y": 2.3, "z": 0.1, "horizontal": 2.3},
    "attitude": {"pitch": -2.1, "roll": 0.8, "yaw": 0.0},
    "phoneLocation": {
        "latitude": HOME_LAT,
        "longitude": HOME_LON,
        "heading": 90.0,
        "pressure": 1013.2,
        "battery": 78,
        "wifiRssi": -55,
    },
    "webRtc": {},
    "gimbalAttitude": {"pitch": -30.0, "roll": 0.0, "yaw": 0.0},
    "gimbalJointAttitude": {"pitch": -30.0, "roll": 0.0, "yaw": 0.0},
    "zoomFl": 24.0,
    "hybridFl": 24.0,
    "opticalFl": 24.0,
    "zoomRatio": 1.0,
    "satelliteCount": 14,
    "homeLocation": {"latitude": HOME_LAT, "longitude": HOME_LON},
    "waypointReached": False,
    "intermediaryWaypointReached": False,
    "yawReached": True,
    "altitudeReached": True,
    "isRecording": False,
    "homeSet": True,
    "remainingFlightTime": 1320,
    "timeNeededToGoHome": 45,
    "timeNeededToLand": 18,
    "totalTime": 63,
    "maxRadiusCanFlyAndGoHome": 900,
    "batteryNeededToLand": 12,
    "batteryNeededToGoHome": 18,
    "seriousLowBatteryThreshold": 10,
    "lowBatteryThreshold": 20,
    "flightMode": "GPS_NORMAL",
    "fcConnected": True,
    "isFlying": True,
    "isManualOverrideActive": False,
    "autoSensingActive": False,
    "detectedTargets": [],
    "waypointMission": {
        "state": "EXECUTING",
        "currentIndex": 1,
        "missionFile": "spectio_mission.kmz",
    },
}


@dataclass
class Drone:
    name: str
    topic: str
    phase_rad: float
    battery: int
    battery_dir: int
    alt_phase: float = 0.0


def _load_dotenv(path: Path) -> None:
    """Carrega KEY=VALUE do .env para os.environ (sem depender de python-dotenv)."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def meters_to_latlon(dx_m: float, dy_m: float) -> tuple[float, float]:
    cos_lat = math.cos(math.radians(CENTER_LAT))
    lat = CENTER_LAT + dy_m / METERS_PER_DEG_LAT
    lon = CENTER_LON + dx_m / (METERS_PER_DEG_LAT * cos_lat)
    return lat, lon


def circle_pose(phase_rad: float, t: float) -> tuple[float, float, float, float, float]:
    theta = phase_rad + ORBIT_OMEGA * t
    east = RADIUS_M * math.cos(theta)
    north = RADIUS_M * math.sin(theta)
    lat, lon = meters_to_latlon(east, north)
    v = RADIUS_M * ORBIT_OMEGA
    vx = -v * math.sin(theta)
    vy = v * math.cos(theta)
    heading = (math.degrees(math.atan2(vx, vy)) + 360.0) % 360.0
    return lat, lon, heading, vx, vy


def step_battery(drone: Drone) -> None:
    drone.battery += drone.battery_dir
    if drone.battery <= BATTERY_MIN:
        drone.battery = BATTERY_MIN
        drone.battery_dir = 1
    elif drone.battery >= BATTERY_MAX:
        drone.battery = BATTERY_MAX
        drone.battery_dir = -1


def altitude_agl(t: float, span_m: float, phase: float) -> float:
    """Oscila BASE_AGL ± span/2 (peak-to-peak = span_m). Período ~40 s."""
    if span_m <= 0:
        return BASE_AGL
    half = span_m / 2.0
    return BASE_AGL + half * math.sin(2 * math.pi * t / 40.0 + phase)


def build_payload(
    drone: Drone,
    t: float,
    now_ms: int,
    *,
    mode: str,
    altitude_span: float,
) -> dict:
    lat, lon, heading, vx, vy = circle_pose(drone.phase_rad, t)
    speed_h = math.hypot(vx, vy)
    dist_home = math.hypot(
        (lon - HOME_LON) * METERS_PER_DEG_LAT * math.cos(math.radians(CENTER_LAT)),
        (lat - HOME_LAT) * METERS_PER_DEG_LAT,
    )

    if mode in ("altitude", "both"):
        agl = altitude_agl(t, altitude_span, drone.alt_phase)
    else:
        agl = BASE_AGL
    msl = CENTER_ALT + (agl - BASE_AGL)

    payload = deepcopy(BASE_PAYLOAD)
    payload.update(
        {
            "droneName": drone.name,
            "heading": round(heading, 2),
            "attitude": {"pitch": -2.1, "roll": 0.8, "yaw": round(heading, 2)},
            "speed": {
                "x": round(vx, 3),
                "y": round(vy, 3),
                "z": 0.1,
                "horizontal": round(speed_h, 3),
            },
            "location": {
                "latitude": round(lat, 7),
                "longitude": round(lon, 7),
                "altitude": round(msl, 2),
            },
            "altitudeAGL": round(agl, 2),
            "gimbalAttitude": {"pitch": -30.0, "roll": 0.0, "yaw": round(heading - 0.5, 2)},
            "gimbalJointAttitude": {
                "pitch": -30.0,
                "roll": 0.0,
                "yaw": round(heading - 0.5, 2),
            },
            "batteryLevel": drone.battery,
            "remainingCharge": drone.battery,
            "distanceToHome": round(dist_home, 2),
            "commandLog": [
                {
                    "ts": now_ms,
                    "command": "takeoff",
                    "source": "mqtt",
                    "status": "ACCEPTED",
                }
            ],
        }
    )
    return payload


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    _load_dotenv(root / ".env")

    p = argparse.ArgumentParser(description="Publica 3 drones simulados no MQTT (ReqValLive).")
    p.add_argument(
        "--broker",
        default=os.environ.get("MQTT_BROKER", "161.24.23.15"),
        help="Host MQTT (default: MQTT_BROKER do .env ou lab Conceptio)",
    )
    p.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MQTT_PORT", "1883")),
    )
    p.add_argument(
        "--username",
        default=os.environ.get("MQTT_USERNAME", "marco"),
    )
    p.add_argument(
        "--password",
        default=os.environ.get("MQTT_PASSWORD", "C1903it@"),
        help="Senha MQTT (prefira MQTT_PASSWORD no .env)",
    )
    p.add_argument(
        "--topic",
        default=os.environ.get("MQTT_TOPIC", "conceptio/reqval"),
        help="Prefixo do tópico; publica em <topic>/drone1|drone2|drone3",
    )
    p.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Intervalo entre publicações (s)",
    )
    p.add_argument(
        "--mode",
        choices=("battery", "altitude", "both"),
        default="both",
        help="O que variar: bateria, altitude AGL, ou ambos",
    )
    p.add_argument(
        "--altitude-span",
        type=float,
        default=2.5,
        help="Amplitude peak-to-peak da altitude AGL em metros (mode altitude/both). "
        "Use >1 para forçar FAIL em range(altitudeAGL)<=1; use 0.5 para PASS.",
    )
    p.add_argument(
        "--client-id",
        default="reqval-three-drones",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if not args.password:
        print(
            "AVISO: MQTT_PASSWORD vazio. Defina no .env ou passe --password.\n"
            "Sem senha a ligação pode falhar no broker do lab.",
            flush=True,
        )

    prefix = args.topic.rstrip("/")
    drones = [
        Drone(
            "dji_mini_4_pro_alpha",
            topic=f"{prefix}/drone1",
            phase_rad=0.0,
            battery=100,
            battery_dir=-1,
            alt_phase=0.0,
        ),
        Drone(
            "dji_mini_4_pro_bravo",
            topic=f"{prefix}/drone2",
            phase_rad=2 * math.pi / 3,
            battery=57,
            battery_dir=-1,
            alt_phase=2.0,
        ),
        Drone(
            "dji_mini_4_pro_charlie",
            topic=f"{prefix}/drone3",
            phase_rad=4 * math.pi / 3,
            battery=15,
            battery_dir=1,
            alt_phase=4.0,
        ),
    ]

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=args.client_id,
    )
    if args.username:
        client.username_pw_set(args.username, args.password or None)
    client.connect(args.broker, args.port, keepalive=60)
    client.loop_start()

    topics = ", ".join(d.topic for d in drones)
    print(
        f"Publicando 3 drones -> {topics}\n"
        f"Broker {args.broker}:{args.port} · mode={args.mode} · "
        f"altitude_span={args.altitude_span} m · intervalo={args.interval}s\n"
        "Na UI do ReqValLive use o MESMO broker/tópico (wildcard # no subscriber).\n"
        "Ctrl+C para parar\n",
        flush=True,
    )

    t0 = time.monotonic()
    try:
        while True:
            t = time.monotonic() - t0
            now_ms = int(time.time() * 1000)
            for drone in drones:
                payload = build_payload(
                    drone,
                    t,
                    now_ms,
                    mode=args.mode,
                    altitude_span=args.altitude_span,
                )
                client.publish(drone.topic, json.dumps(payload), qos=0)
                if args.mode in ("battery", "both"):
                    step_battery(drone)
                print(
                    f"  [{drone.topic}] {drone.name}: bat={drone.battery}%  "
                    f"agl={payload['altitudeAGL']:.2f}  "
                    f"lat={payload['location']['latitude']:.6f}  "
                    f"lon={payload['location']['longitude']:.6f}",
                    flush=True,
                )
            print("---", flush=True)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nEncerrado.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
