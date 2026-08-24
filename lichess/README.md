# Lichess API — Análisis y Automatización

## Parte A — Análisis de partidas (`lichess_analysis.py`)

Descarga las partidas de un usuario, genera estadísticas y visualizaciones.

### Configuración
Edita al inicio del archivo:
- `USERNAME`: usuario de Lichess a analizar
- `MAX_GAMES`: número de partidas a traer

### Ejecución
```bash
pip install pandas matplotlib requests
python lichess_analysis.py
```

### Salidas (carpeta `output/`)
- `partidas.csv` — datos crudos de cada partida
- `estadisticas.csv` — resumen (resultados, rating, color, modo)
- `grafico_resultados.png`, `grafico_rating.png`, `grafico_modos.png`

## Parte B — Automatización de torneos (`lichess_tournaments.py`)

*(pendiente de desarrollo)*

Requiere un token personal de Lichess (Configuración → API access tokens). **No lo pongas directo en el código** — usa una variable de entorno o un archivo `.env` (ya excluido por `.gitignore`).
