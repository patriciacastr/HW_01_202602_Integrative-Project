"""
Parte A - Lichess API: Análisis de partidas
Proyecto Integrador - RPA, APIs y Data Analysis

Este script:
1. Se conecta a la API pública de Lichess
2. Descarga partidas de un usuario configurable
3. Las transforma en un DataFrame de Pandas
4. Genera estadísticas (resultados, rating, color, modo de juego)
5. Crea visualizaciones
6. Exporta datos y estadísticas a CSV
"""

import requests
import pandas as pd
import matplotlib.pyplot as plt
import json
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# CONFIGURACIÓN (edita estos valores según lo que necesites)
# ---------------------------------------------------------------------------
USERNAME_DEFAULT = "Zhigalko_Sergei"   # usuario de Lichess a analizar (configurable)
MAX_GAMES_DEFAULT = 50               # número de partidas a traer (configurable)
OUTPUT_DIR = Path("output")   # carpeta donde se guardan los resultados

OUTPUT_DIR.mkdir(exist_ok=True)

def pedir_configuracion() -> tuple[str, int]:
    """
    Pregunta al usuario, por consola, qué cuenta de Lichess analizar y
    cuántas partidas traer. Si el usuario presiona Enter sin escribir
    nada, se usan los valores por defecto definidos arriba.
    """
    entrada_usuario = input(
        f"Usuario de Lichess a analizar (Enter para usar '{USERNAME_DEFAULT}'): "
    ).strip()
    username = entrada_usuario if entrada_usuario else USERNAME_DEFAULT
 
    entrada_max = input(
        f"Número de partidas a traer (Enter para usar {MAX_GAMES_DEFAULT}): "
    ).strip()
    if entrada_max:
        try:
            max_games = int(entrada_max)
        except ValueError:
            print(f"Valor no numérico, se usará el predeterminado ({MAX_GAMES_DEFAULT}).")
            max_games = MAX_GAMES_DEFAULT
    else:
        max_games = MAX_GAMES_DEFAULT
 
    return username, max_games

# ---------------------------------------------------------------------------
# 1. CONEXIÓN A LA API Y DESCARGA DE PARTIDAS
# ---------------------------------------------------------------------------

def obtener_partidas(username: str, max_games: int) -> list[dict]:
    """
    Llama al endpoint de Lichess que devuelve las partidas de un usuario
    en formato NDJSON.
    """

    url = f"https://lichess.org/api/games/user/{username}"

    params = {
        "max": max_games,
        "opening": True,
        "clocks": False,
        "evals": False,
    }

    token = os.getenv("LICHESS_TOKEN")

    if not token:
        raise RuntimeError(
            "No se encontró LICHESS_TOKEN. "
            "Configura el token como variable de entorno."
        )

    headers = {
        "Accept": "application/x-ndjson",
        "User-Agent": "patriciacastr-lichess-analysis/1.0",
        "Authorization": f"Bearer {token}"
    }

    print(f"Solicitando hasta {max_games} partidas de '{username}'...")

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=30
    )

    if response.status_code == 429:
        raise RuntimeError(
            "Lichess rechazó la solicitud por límite de API (429). "
            "Espera un momento antes de volver a intentarlo."
        )

    response.raise_for_status()

    partidas = []

    for linea in response.text.strip().split("\n"):
        if linea:
            partidas.append(json.loads(linea))

    print(f"Se descargaron {len(partidas)} partidas.")

    return partidas

# ---------------------------------------------------------------------------
# 2. TRANSFORMACIÓN A DATAFRAME
# ---------------------------------------------------------------------------
def construir_dataframe(partidas: list[dict], username: str) -> pd.DataFrame:
    """
    Extrae los campos relevantes de cada partida (JSON anidado) y arma
    una tabla plana con Pandas.
    """
    filas = []
    for p in partidas:
        jugadores = p.get("players", {})
        blancas = jugadores.get("white", {})
        negras = jugadores.get("black", {})

        # Determinar de qué color jugó el usuario analizado
        if blancas.get("user", {}).get("name", "").lower() == username.lower():
            color_usuario = "white"
            rating_usuario = blancas.get("rating")
            rating_rival = negras.get("rating")
        else:
            color_usuario = "black"
            rating_usuario = negras.get("rating")
            rating_rival = blancas.get("rating")

        # Determinar resultado desde la perspectiva del usuario
        ganador = p.get("winner")  # "white", "black" o None (tablas)
        if ganador is None:
            resultado = "draw"
        elif ganador == color_usuario:
            resultado = "win"
        else:
            resultado = "loss"

        filas.append({
            "game_id": p.get("id"),
            "fecha": pd.to_datetime(p.get("createdAt"), unit="ms", errors="coerce"),
            "modo": p.get("speed"),        # bullet, blitz, rapid, classical...
            "variante": p.get("variant"),  # standard, chess960, etc.
            "color": color_usuario,
            "rating_usuario": rating_usuario,
            "rating_rival": rating_rival,
            "resultado": resultado,
            "num_movimientos": len(p.get("moves", "").split()) if p.get("moves") else 0,
        })

    df = pd.DataFrame(filas)
    return df


# ---------------------------------------------------------------------------
# 3. ESTADÍSTICAS
# ---------------------------------------------------------------------------
def generar_estadisticas(df: pd.DataFrame) -> dict:
    stats = {}
    stats["total_partidas"] = len(df)
    stats["resultados"] = df["resultado"].value_counts().to_dict()
    stats["por_color"] = df["color"].value_counts().to_dict()
    stats["por_modo"] = df["modo"].value_counts().to_dict()
    stats["rating_promedio"] = round(df["rating_usuario"].mean(), 1)
    stats["rating_min"] = df["rating_usuario"].min()
    stats["rating_max"] = df["rating_usuario"].max()
    return stats


# ---------------------------------------------------------------------------
# 4. VISUALIZACIONES
# ---------------------------------------------------------------------------
def generar_graficos(df: pd.DataFrame, output_dir: Path):
    # Gráfico 1: distribución de resultados
    plt.figure(figsize=(6, 4))
    df["resultado"].value_counts().plot(kind="bar", color=["seagreen", "indianred", "gray"])
    plt.title("Resultados de las partidas")
    plt.xlabel("Resultado")
    plt.ylabel("Cantidad")
    plt.tight_layout()
    plt.savefig(output_dir / "grafico_resultados.png")
    plt.close()

    # Gráfico 2: evolución del rating a lo largo de las partidas
    plt.figure(figsize=(8, 4))
    df_ordenado = df.sort_values("fecha")
    plt.plot(df_ordenado["fecha"], df_ordenado["rating_usuario"], marker="o", markersize=3)
    plt.title("Evolución del rating")
    plt.xlabel("Fecha")
    plt.ylabel("Rating")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_dir / "grafico_rating.png")
    plt.close()

    # Gráfico 3: partidas por modo de juego
    plt.figure(figsize=(6, 4))
    df["modo"].value_counts().plot(kind="bar", color="steelblue")
    plt.title("Partidas por modo de juego")
    plt.xlabel("Modo")
    plt.ylabel("Cantidad")
    plt.tight_layout()
    plt.savefig(output_dir / "grafico_modos.png")
    plt.close()

    print(f"Gráficos guardados en: {output_dir}")


# ---------------------------------------------------------------------------
# 5. EXPORTACIÓN
# ---------------------------------------------------------------------------
def exportar_resultados(df: pd.DataFrame, stats: dict, output_dir: Path):
    df.to_csv(output_dir / "partidas.csv", index=False)

    # Aplanar el diccionario de stats para guardarlo también como CSV simple
    stats_filas = []
    for clave, valor in stats.items():
        if isinstance(valor, dict):
            for subclave, subvalor in valor.items():
                stats_filas.append({"metrica": f"{clave}_{subclave}", "valor": subvalor})
        else:
            stats_filas.append({"metrica": clave, "valor": valor})

    pd.DataFrame(stats_filas).to_csv(output_dir / "estadisticas.csv", index=False)
    print(f"CSVs guardados en: {output_dir}")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    username, max_games = pedir_configuracion()
    try:
        partidas = obtener_partidas(username, max_games)

    except requests.exceptions.Timeout:
        print("Error: la solicitud a Lichess tardó demasiado.")
        return

    except requests.exceptions.ConnectionError:
        print("Error: no se pudo conectar con Lichess.")
        return

    except requests.exceptions.HTTPError as e:
        print(f"Error HTTP al acceder a Lichess: {e}")
        return

    except RuntimeError as e:
        print(f"Error: {e}")
        return

    if not partidas:
        print("La API no devolvió partidas.")
        return

    df = construir_dataframe(partidas, username)

    stats = generar_estadisticas(df)

    print("\n--- Estadísticas ---")
    for k, v in stats.items():
        print(f"{k}: {v}")

    generar_graficos(df, OUTPUT_DIR)
    exportar_resultados(df, stats, OUTPUT_DIR)

    print("\nProceso completado con éxito.")

if __name__ == "__main__":
    main()
