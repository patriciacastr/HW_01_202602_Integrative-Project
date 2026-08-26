# PeopleSync — RPA de Registro de Nuevo Ingreso

Bot de RPA con Selenium que automatiza el registro de los 50 empleados
del dataset en el formulario PeopleSync HRIS (simulado), campo por campo,
sin intervención manual.

> **Estado:** completo. Probado end-to-end contra el formulario real —
> los registros válidos se cargan y verifican correctamente, y los
> registros con datos inconsistentes (fuera de las opciones reales del
> formulario) se detectan y se saltan sin detener el proceso. Ver
> evidencia en `evidencia_registros.png`.

## Fuente

- Formulario: https://the-paul2002.github.io/Proyecto-IA-/Homework1/
- Dataset (50 registros): Google Sheets — se lee **directo desde la URL
  pública**, sin necesidad de descargar ni mover ningún archivo.

## Requisitos

```bash
pip install selenium pandas
```

Google Chrome instalado (Selenium 4+ gestiona el driver automáticamente).

## Configuración

Todos los parámetros ajustables están al inicio de `peoplesync_bot.py`:

| Variable | Descripción | Default |
|---|---|---|
| `FORM_URL` | URL del formulario a automatizar | (la del enunciado) |
| `SHEET_ID` / `SHEET_GID` | Identifican el Google Sheet del dataset | (el del enunciado) |
| `DATASET_CSV_PATH` | De dónde se lee el dataset — por defecto, la URL de exportación CSV del Sheet. Se puede cambiar a una ruta local (ej. `"dataset.csv"`) si se prefiere | URL de Google Sheets |
| `WAIT_TIMEOUT` | Segundos de espera máxima por elemento (WebDriverWait) | 15 |
| `PAUSE_BETWEEN_RECORDS` | Pausa de cortesía entre cada registro | 1.0s |
| `MODO_INTERACTIVO` | Si es `True`, pausa al final esperando Enter antes de cerrar Chrome (para revisar la tabla en pantalla). Ponerlo en `False` para ejecuciones desatendidas (Task Scheduler) | `True` |
| `EVIDENCIA_PNG` | Nombre del archivo de captura de pantalla final | `evidencia_registros.png` |

## Cómo correrlo

```bash
python peoplesync_bot.py
```

No hace falta descargar el dataset a mano ni recargar el formulario en
ningún momento — todo el proceso corre en una sola carga de página.

## Lógica de validación

Antes de tocar el navegador, cada uno de los 50 registros se valida en
Python contra las **opciones reales** que acepta el formulario (extraídas
directo de su código fuente): DNI de 8 dígitos, teléfono de 9 dígitos
que empieza en 9, correo con formato válido, fechas válidas, y que
Género / Área / Puesto / Tipo de Contrato / Sede / Modalidad sean
exactamente uno de los valores que existen en su `<select>` — el dataset
incluye a propósito valores de Género (`No binario`, `Prefiero no
indicar`) que el formulario no contempla, y esos registros se detectan y
se saltan automáticamente sin interrumpir el resto.

## Verificación de cada registro

Después de enviar el formulario, el script espera (con `WebDriverWait`,
no `time.sleep`) a que el contador "Ingresos registrados hoy" cambie de
valor — esa es la confirmación real de que el registro se guardó, ya que
el formulario no redirige a otra página.

## Salidas

- **Log en consola**: al finalizar, imprime el resumen exigido por el
  enunciado — total de registros procesados, cargados exitosamente,
  no cargados, y el detalle de cada fallo con su DNI/nombre y el motivo
  exacto (dato inválido detectado, o error del formulario).
- **`log_ejecucion.txt`**: la misma salida de consola, guardada
  automáticamente en cada corrida (se sobrescribe cada vez que corres
  el script — no requiere ningún comando especial, ya viene integrado).
- **`evidencia_registros.png`**: captura de pantalla de la tabla final
  de registros, guardada automáticamente antes de cerrar el navegador
  (sirve como evidencia incluso en ejecuciones desatendidas).

## Ejecución automática (Windows Task Scheduler)

Mismo patrón que el proyecto de SUNAT: crear una tarea que ejecute
`python peoplesync_bot.py` desde esta carpeta. Para ejecuciones
desatendidas, poner `MODO_INTERACTIVO = False` en el script (si no, el
proceso queda esperando un Enter que nunca llega).

## Pendiente

- [ ] Configurar y evidenciar la tarea de Windows Task Scheduler (con
      `MODO_INTERACTIVO = False`).
