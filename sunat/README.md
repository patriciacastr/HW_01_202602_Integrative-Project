# SUNAT — Tipo de Cambio Oficial (Web Scraping)

Bot que extrae el tipo de cambio (compra/venta) publicado por SUNAT desde
enero 2024 hasta el mes actual, y lo consolida en un único CSV.

> **Estado:** en desarrollo. La extracción de datos (`extraer_mes_actual`)
> y la navegación mes a mes (`avanzar_un_mes`) están implementadas y
> probadas contra la estructura real del sitio. La selección del mes/año
> inicial (`seleccionar_mes_inicial`) está implementada pero pendiente de
> probar end-to-end. Falta configurar la ejecución automática vía
> Windows Task Scheduler.

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

Por defecto corre con ventana de Chrome visible. Para correrlo sin ventana
(headless, necesario para Task Scheduler), descomentar en el script:

```python
options.add_argument("--headless=new")
```

## Salida

- `tipo_cambio_sunat.csv` — un registro por día, con columnas:
  `fecha, compra, venta, publicado, observacion`.
- Log en consola con resumen final: meses procesados, meses fallidos y el
  motivo de cada falla (el proceso no se detiene si un mes individual falla).

## Pendiente

- [ ] Probar `seleccionar_mes_inicial` end-to-end contra el sitio real.
- [ ] Ajustar `avanzar_un_mes` a un `WebDriverWait` explícito en vez de
      `time.sleep` fijo, si hace falta.
- [ ] Configurar tarea en Windows Task Scheduler (intérprete de Python,
      ruta absoluta del script, ruta absoluta de salida).
- [ ] Evidencia de ejecución automática vía Task Scheduler.
