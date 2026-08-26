# SUNAT — Tipo de Cambio Oficial (Web Scraping)

Bot que extrae el tipo de cambio (compra/venta) publicado por SUNAT desde
enero 2024 hasta el mes actual, y lo consolida en un único CSV.

> **Estado:** completo. Extracción, navegación mes a mes, filtro de días
> duplicados y guardado en CSV probados end-to-end con el rango completo
> (enero 2024 → mes actual, 974 registros, sin meses fallidos). Ejecución
> automática vía Windows Task Scheduler configurada y probada (ver
> sección "Ejecución automática" abajo).

## Fuente

https://e-consulta.sunat.gob.pe/cl-at-ittipcam/tcS01Alias

## Requisitos

- Python 3.10+
- Google Chrome instalado
- Dependencias del archivo `requirements.txt`:

```bash
pip install -r requirements.txt
```

Selenium 4+ gestiona el driver de Chrome automáticamente (no hace falta
descargar ChromeDriver aparte).

## Configuración

Todos los parámetros ajustables están al inicio de `sunat_scraper.py`:

| Variable | Descripción | Default |
|---|---|---|
| `START_YEAR` / `START_MONTH` | Mes/año desde donde empieza la extracción | 2024 / enero |
| `OUTPUT_CSV` | Nombre del archivo de salida | `tipo_cambio_sunat.csv` |
| `WAIT_TIMEOUT` | Segundos de espera máxima por elemento (WebDriverWait) | 15 |
| `PAUSE_BETWEEN_MONTHS` | Pausa de cortesía entre cada mes consultado (no saturar el servidor) | 1.5s |

El rango final siempre llega hasta el mes actual (calculado automáticamente
con la fecha del sistema — no hay que tocar nada cada mes).

## Cómo correrlo

```bash
python sunat_scraper.py
```

Corre con ventana de Chrome visible (no headless). El sitio de SUNAT
bloquea las conexiones en modo headless (`ERR_EMPTY_RESPONSE`, probablemente
por fingerprinting a nivel de red), así que se descartó ese modo. Esto no es
un problema para la ejecución automática: ver la siguiente sección.

## Ejecución automática (Windows Task Scheduler)

`run_sunat.bat` (en esta misma carpeta) es el punto de entrada para Task
Scheduler: se ubica solo en la carpeta del proyecto, corre el script y
guarda toda la salida en `logs/run_log.txt` con fecha y hora de cada
ejecución.

Configuración de la tarea:
- **Acción:** iniciar programa → ruta completa a `run_sunat.bat`.
- **Configuración de sesión:** "Ejecutar solo cuando el usuario haya
  iniciado sesión" (la cuenta de Windows usada no tiene contraseña, así
  que la opción "ejecutar con o sin sesión iniciada" no es utilizable
  aquí — esa opción requiere una contraseña guardada).
- Como corre en modo visible (no headless), al dispararse la tarea se
  ve a Chrome abrirse y operar solo, sin intervención manual — esa es
  la evidencia de que el proceso se ejecuta automáticamente.

Probado con "Ejecutar" manual desde Task Scheduler: corrió los 32 meses
completos y guardó el CSV correctamente, evidenciado en `logs/run_log.txt`.

> Nota: en algunas corridas, la columna "Estado" de Task Scheduler se
> queda mostrando "En ejecución" después de terminar — es un bug visual
> conocido de la interfaz de Windows (no indica que el proceso siga
> corriendo de verdad; se confirma revisando que `run_log.txt` ya tenga
> la línea final "Guardado: ...").

## Salida

- `tipo_cambio_sunat.csv` — un registro por día, con columnas:
  `fecha, compra, venta, publicado, observacion`.
- Log en consola con resumen final: meses procesados, meses fallidos y el
  motivo de cada falla (el proceso no se detiene si un mes individual falla).

## Pendiente

- [x] Probar el flujo completo (navegación mes a mes desde el mes actual
      hasta enero 2024) end-to-end contra el sitio real.
- [x] Configurar tarea en Windows Task Scheduler.
- [x] Evidencia de ejecución automática vía Task Scheduler (`logs/run_log.txt`).
