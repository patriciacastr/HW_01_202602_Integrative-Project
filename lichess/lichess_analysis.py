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
from pathlib import Path

# ---------------------------------------------------------------------------
# CONFIGURACIÓN (edita estos valores según lo que necesites)
# ---------------------------------------------------------------------------
USERNAME = "DrNykterstein"   # usuario de Lichess a analizar (configurable)
MAX_GAMES = 50                # número de partidas a traer (configurable)
OUTPUT_DIR = Path("output")   # carpeta donde se guardan los resultados

OUTPUT_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# 1. CONEXIÓN A LA API Y DESCARGA DE PARTIDAS
# ---------------------------------------------------------------------------
def obtener_partidas(username: str, max_games: int) -> list[dict]:
    """
    Llama al endpoint de Lichess que devuelve las partidas de un usuario
    en formato NDJSON (una partida por línea, en JSON).
    """
    url = f"https://lichess.org/api/games/user/{username}"
    params = {
        "max": max_games,
        "opening": True,
        "clocks": False,
        "evals": False,
    }
    headers = {"Accept": "application/x-ndjson"}

    print(f"Solicitando hasta {max_games} partidas de '{username}'...")
    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()  # lanza error si la petición falló (ej. 404, 500)

    partidas = []
    for linea in response.text.strip().split("\n"):
        if linea:  # ignorar líneas vacías
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
            "num_jugadas": p.get("moves", "").count(" ") + 1 if p.get("moves") else None,
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
    partidas = obtener_partidas(USERNAME, MAX_GAMES)

    if not partidas:
        print("No se encontraron partidas. Verifica el nombre de usuario.")
        return

    df = construir_dataframe(partidas, USERNAME)
    stats = generar_estadisticas(df)

    print("\n--- Estadísticas ---")
    for k, v in stats.items():
        print(f"{k}: {v}")

    generar_graficos(df, OUTPUT_DIR)
    exportar_resultados(df, stats, OUTPUT_DIR)

    print("\nProceso completado con éxito.")


if __name__ == "__main__":
    main()
