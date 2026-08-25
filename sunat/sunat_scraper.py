"""
SUNAT - Tipo de Cambio Oficial - Web Scraper
=============================================
Extrae el tipo de cambio (compra/venta) publicado por SUNAT desde
enero de START_YEAR hasta el mes actual, y consolida todo en un CSV.

Requisitos:
    pip install selenium pandas

Flujo real del sitio (confirmado con pruebas manuales y con el bot):
    - La página, apenas carga, YA MUESTRA el calendario del mes actual
      con sus datos de Compra/Venta (no hace falta tocar el campo
      "Seleccione Mes" ni el botón "Buscar" para nada).
    - Con las flechas '<' (anterior) / '>' (siguiente) se navega mes a
      mes dentro de esa misma tabla, sin recargar la página.
    - Cada celda de día trae su fecha exacta en el atributo
      data-date="YYYY-MM-DDT...Z", así que no hace falta leer el
      encabezado "Mes Año" para saber en qué mes estamos.

Estrategia:
    1. Abrir la página → ya queda parada en el mes actual.
    2. Extraer ese mes.
    3. Calcular cuántos meses hay entre START_YEAR/START_MONTH y hoy.
    4. Hacer esa cantidad de clics en '<' (retroceder), extrayendo en
       cada parada, hasta llegar a START_YEAR/START_MONTH.
    5. Ordenar todo por fecha y guardar el CSV.

Nota: se descartó usar el popup "Seleccione Mes" + botón "Buscar"
porque su selector de mes/año es un widget dinámico frágil de
automatizar de forma confiable; navegar con las flechas desde el mes
actual (que ya viene cargado) es más simple y robusto.
"""

import time
import csv
from datetime import date
from dataclasses import dataclass, asdict

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ----------------------------------------------------------------------
# CONFIGURACIÓN (mantener editable, sin hardcodear rutas de usuario)
# ----------------------------------------------------------------------
URL = "https://e-consulta.sunat.gob.pe/cl-at-ittipcam/tcS01Alias"
START_YEAR = 2024
START_MONTH = 1  # enero
OUTPUT_CSV = "tipo_cambio_sunat.csv"
WAIT_TIMEOUT = 15           # segundos para WebDriverWait
PAUSE_BETWEEN_MONTHS = 1.5  # segundos de cortesía entre cada clic (no saturar el servidor)

# Selectores confirmados inspeccionando la página real
SEL_CELDAS_DIA = (By.CSS_SELECTOR, "td.calendar-day.current.js-cal-option[data-date]")
SEL_FLECHA_ANTERIOR = (By.CSS_SELECTOR, "button.js-cal-prev")
SEL_FLECHA_SIGUIENTE = (By.CSS_SELECTOR, "button.js-cal-next")


@dataclass
class RegistroTipoCambio:
    fecha: str
    compra: float | None
    venta: float | None
    publicado: bool
    observacion: str = ""


def calcular_meses_a_retroceder(anio_inicio: int, mes_inicio: int) -> int:
    """Cantidad de clics en '<' necesarios desde el mes actual hasta
    (anio_inicio, mes_inicio), inclusive."""
    hoy = date.today()
    return (hoy.year - anio_inicio) * 12 + (hoy.month - mes_inicio)


def crear_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    #options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    options.add_argument("--window-size=1920,1080")  # fuerza viewport grande en headless
    # Oculta señales de que Chrome está siendo controlado por Selenium
    # (algunos firewalls, como el de SUNAT, cortan la conexión apenas
    # detectan estas banderas de automatización en modo headless).
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(options=options)
    return driver


def abrir_pagina(driver: webdriver.Chrome) -> None:
    """Carga la página. Por defecto ya queda mostrando el calendario
    del mes actual con datos."""
    driver.get(URL)
    try:
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located(SEL_CELDAS_DIA)
        )
    except TimeoutException:
        # --- DEBUG TEMPORAL: si falla, guarda una foto y el HTML
        # completo de lo que Chrome realmente recibió, para diagnosticar
        # (útil sobre todo en modo headless, donde no vemos la pantalla).
        # Borrar este bloque cuando ya no haga falta.
        driver.save_screenshot("debug_headless.png")
        with open("debug_headless.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("DEBUG: guardé debug_headless.png y debug_headless.html")
        # --- FIN DEBUG TEMPORAL ---
        raise


def extraer_mes_actual(driver: webdriver.Chrome) -> list[RegistroTipoCambio]:
    """Lee todas las celdas de día visibles y arma los registros del mes."""
    registros: list[RegistroTipoCambio] = []
    celdas = driver.find_elements(*SEL_CELDAS_DIA)

    for celda in celdas:
        fecha_raw = celda.get_attribute("data-date")  # "2025-01-02T05:00:00.000Z"
        if not fecha_raw:
            continue
        fecha = fecha_raw.split("T")[0]  # "2025-01-02"

        compra = None
        venta = None
        try:
            compra_txt = celda.find_element(
                By.CSS_SELECTOR, "div.normal-all-day"
            ).text
            compra = float(compra_txt.replace("Compra", "").strip())
        except (NoSuchElementException, ValueError):
            pass

        try:
            venta_txt = celda.find_element(
                By.CSS_SELECTOR, "div.pap-all-day"
            ).text
            venta = float(venta_txt.replace("Venta", "").strip())
        except (NoSuchElementException, ValueError):
            pass

        publicado = compra is not None and venta is not None
        obs = "" if publicado else "Sin tipo de cambio publicado / feriado"

        registros.append(
            RegistroTipoCambio(
                fecha=fecha, compra=compra, venta=venta,
                publicado=publicado, observacion=obs,
            )
        )

    return registros


def retroceder_un_mes(driver: webdriver.Chrome) -> None:
    wait = WebDriverWait(driver, WAIT_TIMEOUT)
    # Guardamos una celda actual para poder esperar a que "muera"
    # (quede obsoleta) cuando el calendario repinte con el nuevo mes.
    celdas_antes = driver.find_elements(*SEL_CELDAS_DIA)
    primera_celda_antes = celdas_antes[0] if celdas_antes else None

    flecha = wait.until(EC.element_to_be_clickable(SEL_FLECHA_ANTERIOR))
    flecha.click()

    if primera_celda_antes is not None:
        try:
            wait.until(EC.staleness_of(primera_celda_antes))
        except TimeoutException:
            pass  # si no detecta staleness, seguimos con el sleep de cortesía

    time.sleep(PAUSE_BETWEEN_MONTHS)


def guardar_csv(todos_los_registros: list[RegistroTipoCambio], ruta: str) -> None:
    registros_ordenados = sorted(todos_los_registros, key=lambda r: r.fecha)
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(asdict(registros_ordenados[0]).keys())
        )
        writer.writeheader()
        for r in registros_ordenados:
            writer.writerow(asdict(r))


def main() -> None:
    meses_a_retroceder = calcular_meses_a_retroceder(START_YEAR, START_MONTH)
    print(f"Meses a extraer: {meses_a_retroceder + 1} "
          f"(desde {START_MONTH:02d}/{START_YEAR} hasta el mes actual)")

    driver = crear_driver()
    todos_los_registros: list[RegistroTipoCambio] = []
    meses_fallidos: list[str] = []

    try:
        abrir_pagina(driver)

        for i in range(meses_a_retroceder + 1):
            try:
                registros_mes = extraer_mes_actual(driver)
                todos_los_registros.extend(registros_mes)
                print(f"  Mes {i + 1}/{meses_a_retroceder + 1}: "
                      f"{len(registros_mes)} días extraídos")
            except TimeoutException:
                meses_fallidos.append(f"Iteración {i + 1}: timeout esperando la tabla")
                print(f"  Mes {i + 1}: FALLÓ (timeout)")

            if i < meses_a_retroceder:
                retroceder_un_mes(driver)

    finally:
        driver.quit()

    if todos_los_registros:
        guardar_csv(todos_los_registros, OUTPUT_CSV)
        print(f"\nGuardado: {OUTPUT_CSV} ({len(todos_los_registros)} registros)")
    else:
        print("\nNo se extrajo ningún registro.")

    if meses_fallidos:
        print(f"\nMeses con error ({len(meses_fallidos)}):")
        for m in meses_fallidos:
            print(f"  - {m}")


if __name__ == "__main__":
    main()
