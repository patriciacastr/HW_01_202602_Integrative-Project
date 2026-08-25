"""
Parte B - Lichess API: Automatización de torneos
Proyecto Integrador - RPA, APIs y Data Analysis

Este script:
1. Define un calendario semanal de torneos (día, hora, modo, duración, variante)
2. Se conecta a la API de torneos de Lichess con autenticación
3. Crea automáticamente cada torneo mediante la API
4. Salta los torneos cuya hora de inicio ya pasó
5. Incluye un modo de simulación (dry-run)
6. Maneja errores de API sin detener la ejecución completa
"""

import os
import requests
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------------
DRY_RUN = True  # True = solo simula (no crea torneos reales). Cambiar a False para crear de verdad. False = lo hace real.

API_URL = "https://lichess.org/api/tournament"

# Calendario semanal de torneos: cada entrada define un torneo recurrente.
# "dia_semana": 0=lunes, 1=martes, ..., 6=domingo (estándar de Python/datetime)
CALENDARIO_SEMANAL = [
    {
        "nombre": "Torneo Blitz de los Lunes",
        "dia_semana": 0,
        "hora": "18:00",
        "modo": "blitz",       # clockTime/clockIncrement definidos abajo según el modo
        "duracion_min": 60,
        "variante": "standard",
        "rated": True,
    },
    {
        "nombre": "Torneo Rapid de los Miércoles",
        "dia_semana": 2,
        "hora": "19:00",
        "modo": "rapid",
        "duracion_min": 90,
        "variante": "standard",
        "rated": True,
    },
    {
        "nombre": "Torneo Bullet del Viernes",
        "dia_semana": 4,
        "hora": "20:00",
        "modo": "bullet",
        "duracion_min": 45,
        "variante": "standard",
        "rated": False,
    },
]

# Configuración de reloj según el modo de juego (minutos, incremento en segundos)
CONFIG_MODO = {
    "bullet": {"clockTime": 1, "clockIncrement": 0},
    "blitz": {"clockTime": 5, "clockIncrement": 3},
    "rapid": {"clockTime": 10, "clockIncrement": 5},
    "classical": {"clockTime": 30, "clockIncrement": 20},
}


# ---------------------------------------------------------------------------
# UTILIDADES DE FECHA
# ---------------------------------------------------------------------------
def proxima_ocurrencia(dia_semana: int, hora_str: str) -> datetime:
    """
    Dado un día de la semana (0=lunes) y una hora ("HH:MM"), calcula la
    próxima fecha/hora futura en que ocurre (esta semana o la siguiente
    si ya pasó).
    """
    ahora = datetime.now(timezone.utc)
    hora, minuto = map(int, hora_str.split(":"))

    dias_para_sumar = (dia_semana - ahora.weekday()) % 7
    candidato = ahora.replace(hour=hora, minute=minuto, second=0, microsecond=0) + timedelta(days=dias_para_sumar)

    if candidato <= ahora:
        candidato += timedelta(days=7)

    return candidato


# ---------------------------------------------------------------------------
# CREACIÓN DE TORNEOS
# ---------------------------------------------------------------------------
def crear_torneo(torneo: dict, headers: dict, dry_run: bool) -> dict:
    """
    Crea un torneo en Lichess a partir de la configuración dada.
    Si dry_run=True, no hace la petición real, solo la simula.
    """
    fecha_inicio = proxima_ocurrencia(torneo["dia_semana"], torneo["hora"])
    config_reloj = CONFIG_MODO[torneo["modo"]]

    payload = {
        "name": torneo["nombre"],
        "clockTime": config_reloj["clockTime"],
        "clockIncrement": config_reloj["clockIncrement"],
        "minutes": torneo["duracion_min"],
        "startDate": int(fecha_inicio.timestamp() * 1000),  # Lichess espera epoch en milisegundos
        "variant": torneo["variante"],
        "rated": str(torneo["rated"]).lower(),
    }

    print(f"\n--- {torneo['nombre']} ---")
    print(f"Programado para: {fecha_inicio.strftime('%A %d/%m/%Y %H:%M UTC')}")

    if dry_run:
        print("[DRY-RUN] No se creó el torneo de verdad. Payload que se habría enviado:")
        print(payload)
        return {"status": "simulado", "nombre": torneo["nombre"], "fecha": fecha_inicio}

    try:
        response = requests.post(API_URL, data=payload, headers=headers, timeout=30)

        if response.status_code == 401:
            raise RuntimeError(
                "No autorizado (401). Verifica que tu token tenga el permiso "
                "'tournament:write'."
            )

        response.raise_for_status()
        data = response.json()
        print(f"Torneo creado correctamente. ID: {data.get('id')}")
        return {"status": "creado", "nombre": torneo["nombre"], "id": data.get("id")}

    except requests.exceptions.HTTPError as e:
        print(f"Error HTTP al crear el torneo: {e}")
        return {"status": "error", "nombre": torneo["nombre"], "motivo": str(e)}
    except RuntimeError as e:
        print(f"Error: {e}")
        return {"status": "error", "nombre": torneo["nombre"], "motivo": str(e)}
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")
        return {"status": "error", "nombre": torneo["nombre"], "motivo": str(e)}


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    token = os.getenv("LICHESS_TOKEN")
    if not token:
        print("Error: no se encontró LICHESS_TOKEN como variable de entorno.")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "lichess-tournaments/1.0",
    }

    print(f"Modo: {'DRY-RUN (simulación)' if DRY_RUN else 'REAL (se crearán torneos de verdad)'}")

    resultados = []
    for torneo in CALENDARIO_SEMANAL:
        resultado = crear_torneo(torneo, headers, DRY_RUN)
        resultados.append(resultado)

    print("\n--- Resumen ---")
    creados = sum(1 for r in resultados if r["status"] in ("creado", "simulado"))
    errores = sum(1 for r in resultados if r["status"] == "error")
    print(f"Total procesados: {len(resultados)}")
    print(f"Exitosos/simulados: {creados}")
    print(f"Con error: {errores}")

    if errores:
        print("\nDetalle de errores:")
        for r in resultados:
            if r["status"] == "error":
                print(f"  - {r['nombre']}: {r['motivo']}")


if __name__ == "__main__":
    main()
