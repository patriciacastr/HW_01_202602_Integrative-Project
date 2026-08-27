# HW_01_202602 — Integrative Project

Proyecto integrador de automatización, APIs y análisis de datos. Consta de tres partes independientes:

| Proyecto | Carpeta | Descripción | Puntos |
|---|---|---|---|
| RPA — PeopleSync ✅| [`/peoplesync`](./peoplesync) | Automatización con Selenium del registro de 50 empleados |
| Web Scraping — SUNAT ✅ | [`/sunat`](./sunat) | Extracción del tipo de cambio oficial (ene 2024–actual) |
| Lichess API ✅ | [`/lichess`](./lichess) | Análisis de partidas y automatización de torneos vía API | 

## Estructura del repositorio

```
HW_01_202602_Integrative-Project/
├── README.md                  <- este archivo
├── .gitignore
├── peoplesync/
│   ├── peoplesync_bot.py
│   ├── dataset en google sheets   <- 50 registros de entrada
│   ├── logs/                      <- logs de ejecución
│   └── README.md                  <- instrucciones específicas
├── sunat/
│   ├── sunat_scraper.py
│   ├── run_sunat.bat          <- entry point para Task Scheduler
│   ├── requirements.txt
│   ├── tipo_cambio_sunat.csv  <- CSV consolidado (974 registros)
│   ├── logs/                  <- logs de ejecución (run_log.txt)
│   └── README.md
└── lichess/
    ├── lichess_analysis.py    <- Parte A: análisis de partidas
    ├── lichess_tournaments.py <- Parte B: automatización de torneos
    ├── output/                <- CSVs y gráficos generados
    └── README.md
```

## Requisitos generales

- Python 3.10+
- Instalar dependencias: `pip install -r requirements.txt` (ver cada subcarpeta)
- Google Chrome + ChromeDriver (para los proyectos con Selenium)


[Ver video](#)

## Autor

- Patricia Castro Hilario — Universidad del Pacífico
- Carla Bocanegra Valentin — Universidad del Pacífico
