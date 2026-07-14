"""Publica telemetria de 3 drones no MQTT (mesmo círculo, baterias em fase).

Broker: 161.24.23.15:1883
Tópicos: conceptio/reqval/drone1|drone2|drone3
Bateria: 100% <-> 15% a 1%/s (fases distintas por drone).
Posição: órbita circular com 120° de separação (sem colisão).
"""

from __future__ import annotations

import json
import math
import time
from copy import deepcopy
from dataclasses import dataclass

from paho.mqtt import client as mqtt

BROKER = "161.24.23.15"
PORT = 1883
TOPIC_PREFIX = "conceptio/reqval"
USERNAME = "marco"
PASSWORD = "C1903it@"
INTERVAL_S = 1.0

# Centro do círculo (São José dos Campos — payload de referência)
CENTER_LAT = -23.189612
CENTER_LON = -45.884123
CENTER_ALT = 612.4
HOME_LAT = -23.189600
HOME_LON = -45.884100

RADIUS_M = 60.0  # mesmos drones no mesmo círculo; ~60 m entre vizinhos
ORBIT_OMEGA = 2 * math.pi / 90.0  # 1 volta a cada 90 s
METERS_PER_DEG_LAT = 111_320.0

BATTERY_MIN = 15
BATTERY_MAX = 100


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
    phase_rad: float  # offset angular no círculo
    battery: int
    battery_dir: int  # -1 descendo, +1 subindo


def meters_to_latlon(dx_m: float, dy_m: float) -> tuple[float, float]:
    """dx = east, dy = north → (lat, lon)."""
    cos_lat = math.cos(math.radians(CENTER_LAT))
    lat = CENTER_LAT + dy_m / METERS_PER_DEG_LAT
    lon = CENTER_LON + dx_m / (METERS_PER_DEG_LAT * cos_lat)
    return lat, lon


def circle_pose(phase_rad: float, t: float) -> tuple[float, float, float, float, float]:
    """Retorna lat, lon, heading_deg, vx, vy (ENU m/s)."""
    theta = phase_rad + ORBIT_OMEGA * t
    # posição relativa ao centro (leste / norte)
    east = RADIUS_M * math.cos(theta)
    north = RADIUS_M * math.sin(theta)
    lat, lon = meters_to_latlon(east, north)

    # velocidade tangencial (sentido anti-horário)
    v = RADIUS_M * ORBIT_OMEGA
    vx = -v * math.sin(theta)  # east
    vy = v * math.cos(theta)  # north
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


def build_payload(drone: Drone, t: float, now_ms: int) -> dict:
    lat, lon, heading, vx, vy = circle_pose(drone.phase_rad, t)
    speed_h = math.hypot(vx, vy)
    dist_home = math.hypot(
        (lon - HOME_LON) * METERS_PER_DEG_LAT * math.cos(math.radians(CENTER_LAT)),
        (lat - HOME_LAT) * METERS_PER_DEG_LAT,
    )

    payload = deepcopy(BASE_PAYLOAD)
    payload.update(
        {
            "droneName": drone.name,
            "heading": round(heading, 2),
            "attitude": {
                "pitch": -2.1,
                "roll": 0.8,
                "yaw": round(heading, 2),
            },
            "speed": {
                "x": round(vx, 3),
                "y": round(vy, 3),
                "z": 0.1,
                "horizontal": round(speed_h, 3),
            },
            "location": {
                "latitude": round(lat, 7),
                "longitude": round(lon, 7),
                "altitude": CENTER_ALT,
            },
            "altitudeAGL": 24.5,
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


def main() -> None:
    # 120° de fase → ~60√3 ≈ 104 m de distância cordal (sem colisão)
    drones = [
        Drone(
            "dji_mini_4_pro_alpha",
            topic=f"{TOPIC_PREFIX}/drone1",
            phase_rad=0.0,
            battery=100,
            battery_dir=-1,
        ),
        Drone(
            "dji_mini_4_pro_bravo",
            topic=f"{TOPIC_PREFIX}/drone2",
            phase_rad=2 * math.pi / 3,
            battery=57,
            battery_dir=-1,
        ),
        Drone(
            "dji_mini_4_pro_charlie",
            topic=f"{TOPIC_PREFIX}/drone3",
            phase_rad=4 * math.pi / 3,
            battery=15,
            battery_dir=1,
        ),
    ]

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="reqval-three-drones",
    )
    client.username_pw_set(USERNAME, PASSWORD)
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()

    topics = ", ".join(d.topic for d in drones)
    print(
        f"Publicando 3 drones -> {topics} @ {BROKER}:{PORT}\n"
        f"Circulo r={RADIUS_M} m | bateria {BATTERY_MAX}<->{BATTERY_MIN} @ 1%/s\n"
        "Ctrl+C para parar\n",
        flush=True,
    )

    t0 = time.monotonic()
    try:
        while True:
            t = time.monotonic() - t0
            now_ms = int(time.time() * 1000)
            for drone in drones:
                payload = build_payload(drone, t, now_ms)
                client.publish(drone.topic, json.dumps(payload), qos=0)
                step_battery(drone)
                print(
                    f"  [{drone.topic}] {drone.name}: bat={drone.battery}%  "
                    f"lat={payload['location']['latitude']:.6f}  "
                    f"lon={payload['location']['longitude']:.6f}  "
                    f"hdg={payload['heading']:.1f}",
                    flush=True,
                )
            print("---", flush=True)
            time.sleep(INTERVAL_S)
    except KeyboardInterrupt:
        print("\nEncerrado.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
