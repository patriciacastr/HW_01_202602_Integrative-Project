"""
PeopleSync - RPA de Registro de Nuevo Ingreso
==============================================
Automatiza el registro de empleados en el formulario PeopleSync HRIS
a partir de un dataset (CSV), usando Selenium.

Requisitos:
    pip install selenium pandas

Flujo:
    1. Lee el dataset (CSV con las columnas: apellidos_nombres, dni,
    fecha_nacimiento, genero, telefono, correo, area, puesto,
    contrato, sede, fecha_ingreso, modalidad).
    2. Valida cada registro en Python ANTES de tocar el navegador
    (contra los valores reales que acepta cada <select> del
    formulario, más formato de DNI/teléfono/correo/fechas). Los
    registros inválidos se saltan sin intentar cargarlos.
    3. Para cada registro válido: llena el formulario, envía, y
    verifica que el contador de "Ingresos registrados" haya subido
    (confirmación de que el registro se guardó).
    4. Todo en una sola carga de página (sin recargar manualmente).
    5. Al final, imprime un log con: total procesados, exitosos,
    fallidos, y el detalle de cada fallo (identificador + motivo).
"""

import re
import time
from datetime import datetime
from dataclasses import dataclass

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ----------------------------------------------------------------------
# CONFIGURACIÓN (editable, sin hardcodear rutas de usuario)
# ----------------------------------------------------------------------
FORM_URL = "https://the-paul2002.github.io/Proyecto-IA-/Homework1/"

# Dataset: se lee directo desde Google Sheets (el Sheet es público), como
# CSV exportado por Google — no hace falta descargar nada a mano.
# Si prefieres usar un archivo local en vez de la URL, solo cambia esta
# variable a la ruta del .csv (ej. "dataset.csv").
SHEET_ID = "1EjaoSJKdzdUBNF3XJZuTlxA21D-0vy0wkGaMR8wHVgs"
SHEET_GID = "0"
DATASET_CSV_PATH = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"

WAIT_TIMEOUT = 15
PAUSE_BETWEEN_RECORDS = 1.0  # segundos de cortesía entre cada registro

# Si es True, al terminar el script espera a que presiones Enter antes de
# cerrar Chrome (para que puedas revisar la tabla de registros en pantalla).
# Ponlo en False para ejecuciones desatendidas (ej. Windows Task Scheduler),
# donde no hay nadie para presionar Enter. De todas formas, siempre se
# guarda una captura de pantalla final como evidencia (ver EVIDENCIA_PNG).
MODO_INTERACTIVO = True
EVIDENCIA_PNG = "evidencia_registros.png"

# ----------------------------------------------------------------------
# Valores válidos reales (extraídos del <select> del formulario) —
# se usan para pre-validar antes de tocar el navegador.
# ----------------------------------------------------------------------
GENEROS_VALIDOS = {"Masculino", "Femenino"}

AREAS_VALIDAS = {
    "Recursos Humanos", "Finanzas y Contabilidad", "Tecnología e Innovación",
    "Operaciones", "Comercial y Ventas", "Marketing", "Legal y Cumplimiento",
    "Logística y Supply Chain", "Servicio al Cliente", "Gerencia General",
}

PUESTOS_VALIDOS = {
    "Analista Jr.", "Analista", "Analista Sr.", "Analista de Datos",
    "Analista de RRHH", "Analista Financiero",
    "Especialista en TI", "Especialista Legal", "Especialista en Marketing",
    "Especialista en Logística",
    "Coordinador de Área", "Coordinador Comercial", "Coordinador de Proyectos",
    "Jefe de Área", "Gerente de Área", "Sub Gerente",
    "Asistente Administrativo", "Practicante Profesional",
    "Practicante Preprofesional",
}

CONTRATOS_VALIDOS = {
    "Planilla Fija", "Contrato por Servicios", "Practicante Profesional",
    "Practicante Preprofesional", "Contrato a Plazo Fijo", "Part-time",
}

SEDES_VALIDAS = {
    "Lima - San Isidro (Sede Central)", "Lima - Miraflores",
    "Lima - La Molina", "Lima - Callao",
    "Arequipa", "Trujillo", "Cusco", "Piura", "Chiclayo",
}

MODALIDADES_VALIDAS = {"Presencial", "Remoto", "Híbrido"}

# Selectores del formulario (id reales, del código fuente)
SEL_NOMBRES = (By.ID, "nombres")
SEL_DNI = (By.ID, "dni")
SEL_FECHA_NAC = (By.ID, "fecha_nacimiento")
SEL_GENERO = (By.ID, "genero")
SEL_TELEFONO = (By.ID, "telefono")
SEL_CORREO = (By.ID, "correo")
SEL_AREA = (By.ID, "area")
SEL_PUESTO = (By.ID, "puesto")
SEL_CONTRATO = (By.ID, "contrato")
SEL_SEDE = (By.ID, "sede")
SEL_FECHA_INGRESO = (By.ID, "fecha_ingreso")
SEL_BOTON_REGISTRAR = (By.ID, "btn-registrar")
SEL_CONTADOR = (By.ID, "counter")


@dataclass
class RegistroFallido:
    identificador: str
    motivo: str


# ----------------------------------------------------------------------
# 1. LECTURA Y VALIDACIÓN DEL DATASET
# ----------------------------------------------------------------------
def leer_dataset(ruta: str) -> pd.DataFrame:
    df = pd.read_csv(ruta, dtype=str).fillna("")
    return df


def convertir_fecha(fecha_str: str) -> str | None:
    """Convierte DD/MM/YYYY (formato del dataset) a YYYY-MM-DD
    (formato que requiere el <input type="date">). Devuelve None si
    la fecha no es válida."""
    try:
        return datetime.strptime(fecha_str.strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        return None


def validar_registro(fila: dict) -> list[str]:
    """Valida un registro contra las reglas reales del formulario.
    Devuelve una lista de motivos de error (vacía si todo está bien)."""
    errores = []

    if not fila.get("apellidos_nombres", "").strip():
        errores.append("apellidos_nombres vacío")

    dni = fila.get("dni", "").strip()
    if not re.fullmatch(r"\d{8}", dni):
        errores.append(f"DNI inválido ('{dni}', debe ser 8 dígitos)")

    if convertir_fecha(fila.get("fecha_nacimiento", "")) is None:
        errores.append(
            f"fecha_nacimiento inválida ('{fila.get('fecha_nacimiento')}')")

    genero = fila.get("genero", "").strip()
    if genero not in GENEROS_VALIDOS:
        errores.append(f"genero no soportado por el formulario ('{genero}')")

    telefono = fila.get("telefono", "").strip()
    if not re.fullmatch(r"9\d{8}", telefono):
        errores.append(
            f"telefono inválido ('{telefono}', debe ser 9 dígitos empezando en 9)")

    correo = fila.get("correo", "").strip()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", correo):
        errores.append(f"correo inválido ('{correo}')")

    area = fila.get("area", "").strip()
    if area not in AREAS_VALIDAS:
        errores.append(f"area no soportada por el formulario ('{area}')")

    puesto = fila.get("puesto", "").strip()
    if puesto not in PUESTOS_VALIDOS:
        errores.append(f"puesto no soportado por el formulario ('{puesto}')")

    contrato = fila.get("contrato", "").strip()
    if contrato not in CONTRATOS_VALIDOS:
        errores.append(
            f"contrato no soportado por el formulario ('{contrato}')")

    sede = fila.get("sede", "").strip()
    if sede not in SEDES_VALIDAS:
        errores.append(f"sede no soportada por el formulario ('{sede}')")

    if convertir_fecha(fila.get("fecha_ingreso", "")) is None:
        errores.append(
            f"fecha_ingreso inválida ('{fila.get('fecha_ingreso')}')")

    modalidad = fila.get("modalidad", "").strip()
    if modalidad not in MODALIDADES_VALIDAS:
        errores.append(
            f"modalidad no soportada por el formulario ('{modalidad}')")

    return errores


# ----------------------------------------------------------------------
# 2. SELENIUM: LLENADO Y ENVÍO
# ----------------------------------------------------------------------
def crear_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1400,1000")
    driver = webdriver.Chrome(options=options)
    return driver


def set_fecha(driver: webdriver.Chrome, locator, fecha_iso: str) -> None:
    """Fija el valor de un <input type='date'> vía JS (evita problemas
    de formato/locale al escribir directo con send_keys)."""
    el = driver.find_element(*locator)
    driver.execute_script("arguments[0].value = arguments[1];", el, fecha_iso)


def marcar_modalidad(driver: webdriver.Chrome, valor: str) -> None:
    """Los radios de modalidad están visualmente ocultos (estilo 'pill'
    con el input en opacity:0), así que se hace clic vía JS para evitar
    problemas de 'elemento no interactuable'."""
    radio = driver.find_element(
        By.CSS_SELECTOR, f'input[name="modalidad"][value="{valor}"]'
    )
    driver.execute_script("arguments[0].click();", radio)


def registrar_empleado(driver: webdriver.Chrome, fila: dict) -> None:
    """Llena y envía el formulario para un registro ya validado.
    Lanza una excepción si algo falla."""
    wait = WebDriverWait(driver, WAIT_TIMEOUT)

    nombres = wait.until(EC.element_to_be_clickable(SEL_NOMBRES))
    nombres.clear()
    nombres.send_keys(fila["apellidos_nombres"].strip())

    dni_el = driver.find_element(*SEL_DNI)
    dni_el.clear()
    dni_el.send_keys(fila["dni"].strip())

    set_fecha(driver, SEL_FECHA_NAC, convertir_fecha(fila["fecha_nacimiento"]))

    Select(driver.find_element(*SEL_GENERO)
           ).select_by_visible_text(fila["genero"].strip())

    tel_el = driver.find_element(*SEL_TELEFONO)
    tel_el.clear()
    tel_el.send_keys(fila["telefono"].strip())

    correo_el = driver.find_element(*SEL_CORREO)
    correo_el.clear()
    correo_el.send_keys(fila["correo"].strip())

    Select(driver.find_element(*SEL_AREA)
           ).select_by_visible_text(fila["area"].strip())
    Select(driver.find_element(*SEL_PUESTO)
           ).select_by_visible_text(fila["puesto"].strip())
    Select(driver.find_element(*SEL_CONTRATO)
           ).select_by_visible_text(fila["contrato"].strip())
    Select(driver.find_element(*SEL_SEDE)
           ).select_by_visible_text(fila["sede"].strip())

    set_fecha(driver, SEL_FECHA_INGRESO,
              convertir_fecha(fila["fecha_ingreso"]))

    marcar_modalidad(driver, fila["modalidad"].strip())

    # Contador ANTES de enviar, para poder confirmar que subió después
    contador_antes = driver.find_element(*SEL_CONTADOR).text

    boton = wait.until(EC.element_to_be_clickable(SEL_BOTON_REGISTRAR))
    boton.click()

    # Verificación: el contador debe cambiar (registro confirmado)
    wait.until(lambda d: d.find_element(*SEL_CONTADOR).text != contador_antes)


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
def main() -> None:
    df = leer_dataset(DATASET_CSV_PATH)
    total = len(df)
    print(f"Registros leídos del dataset: {total}")

    exitosos = 0
    fallidos: list[RegistroFallido] = []

    driver = crear_driver()
    try:
        driver.get(FORM_URL)
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located(SEL_BOTON_REGISTRAR)
        )

        for i, fila in enumerate(df.to_dict(orient="records"), start=1):
            identificador = f"{fila.get('dni', '?')} - {fila.get('apellidos_nombres', '?')}"

            errores = validar_registro(fila)
            if errores:
                motivo = "; ".join(errores)
                print(f"  [{i}/{total}] SALTADO — {identificador}: {motivo}")
                fallidos.append(RegistroFallido(identificador, motivo))
                continue

            try:
                registrar_empleado(driver, fila)
                exitosos += 1
                print(f"  [{i}/{total}] OK — {identificador}")
            except (TimeoutException, NoSuchElementException) as e:
                motivo = f"error en el formulario: {type(e).__name__}"
                print(f"  [{i}/{total}] FALLÓ — {identificador}: {motivo}")
                fallidos.append(RegistroFallido(identificador, motivo))
            except Exception as e:
                motivo = f"error inesperado: {e}"
                print(f"  [{i}/{total}] FALLÓ — {identificador}: {motivo}")
                fallidos.append(RegistroFallido(identificador, motivo))

            time.sleep(PAUSE_BETWEEN_RECORDS)

        # -------------------- LOG FINAL --------------------
        print("\n" + "=" * 60)
        print("RESUMEN FINAL")
        print("=" * 60)
        print(f"Total de registros procesados: {total}")
        print(f"Registros cargados exitosamente: {exitosos}")
        print(f"Registros que no se pudieron cargar: {len(fallidos)}")

        if fallidos:
            print("\nDetalle de registros fallidos:")
            for f in fallidos:
                print(f"  - {f.identificador}: {f.motivo}")

        # -------------------- EVIDENCIA --------------------
        try:
            driver.execute_script(
                "document.getElementById('records-section')?.scrollIntoView();"
            )
            driver.save_screenshot(EVIDENCIA_PNG)
            print(f"\nCaptura de evidencia guardada: {EVIDENCIA_PNG}")
        except Exception:
            pass  # si falla la captura, no interrumpe el cierre del script

        if MODO_INTERACTIVO:
            input("\nPresiona Enter para cerrar el navegador y finalizar...")

    finally:
        # Red de seguridad: el navegador se cierra siempre, incluso si
        # algo falló antes de llegar al resumen.
        driver.quit()


if __name__ == "__main__":
    main()
