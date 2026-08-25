# Lichess API — Análisis y Automatización

## Parte A — Análisis de partidas (`lichess_analysis.py`)

Descarga las partidas de un usuario, genera estadísticas y visualizaciones.

### Configuración
Al ejecutar el script, te pedirá interactivamente:
- Usuario de Lichess a analizar (Enter para usar el valor por defecto)
- Número de partidas a traer (Enter para usar 50)

Requiere un token personal de Lichess con permiso `game:read`, configurado como variable de entorno `LICHESS_TOKEN`.

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

Crea automáticamente un calendario semanal de torneos vía la API de Lichess.

### Configuración
Edita `CALENDARIO_SEMANAL` dentro del archivo para definir tus propios torneos (día, hora, modo, duración, variante, si es rated).

El modo `DRY_RUN` (al inicio del archivo) controla si el script simula (`True`, no crea nada real) o crea los torneos de verdad (`False`).

Requiere el mismo `LICHESS_TOKEN`, pero con el permiso adicional `tournament:write`.

### Ejecución
```bash
python lichess_tournaments.py
```

### Comportamiento
- Calcula automáticamente la próxima fecha/hora futura para cada torneo (salta las que ya pasaron esta semana).
- Maneja errores de API sin detener el resto del calendario.
- Imprime un resumen final: total procesados, exitosos y con error.

**Nota:** dejar `DRY_RUN = True` por defecto para evitar crear torneos duplicados accidentalmente. Cambiar a `False` solo para la demo/evidencia.