# NYC Taxi Cloud Analysis - Grupo 03

Proyecto de análisis de viajes de taxis de Nueva York (NYC TLC) utilizando Google Cloud Platform (GCP), Python y BigQuery. El objetivo es ingestar datos públicos del transporte urbano, limpiar y transformar la información, y dejarla lista para análisis y visualización con herramientas como Power BI o Looker Studio.

## Descripción del proyecto

Este repositorio automatiza un pipeline de datos que:

- descarga archivos Parquet del dataset oficial de TLC de NYC,
- los carga a Google Cloud Storage,
- limpia y transforma los registros,
- genera métricas agregadas por mes,
- sube los resultados a Cloud Storage y BigQuery,
- deja la información preparada para consulta analítica.

La solución está diseñada para manejar datasets de viajes en taxi amarillo de 2025, con foco en indicadores como:

- número de viajes,
- pasajeros promedio,
- distancia promedio,
- ingreso total y promedio,
- duración promedio por viaje,
- distribución por mes.

## Estructura del repositorio

```text
repo-nyc-taxi-cloud-analisis-grupo03/
├── dataset/                          # Datos locales o generados para análisis
├── codigo_fuente/
│   └── transformacion_datos.py      # Limpieza, filtrado y agregación de datos
├── ingesta_datos/
│   ├── ingest_data.py               # Descarga desde TLC y carga a GCS
│   └── requirements.txt             # Dependencias de Python
├── scripts/
│   ├── 04_carga_bigquery.py         # Carga de archivos a BigQuery
│   ├── config.py                    # Configuración base del pipeline
│   ├── pipeline_integration.py      # Orquestador del flujo completo
│   └── run_pipeline.bat             # Script para ejecución en Windows
├── README.md
└── .gitignore
```

## Flujo de trabajo

### 1. Ingesta de datos
El script `ingesta_datos/ingest_data.py` realiza lo siguiente:

- descarga los archivos `.parquet` del portal oficial de TLC,
- valida su estructura y columnas esperadas,
- sube los archivos a un bucket de Google Cloud Storage en la carpeta `raw/`,
- confirma la carga comparando tamaño y metadatos.

### 2. Transformación de datos
El script `codigo_fuente/transformacion_datos.py`:

- carga los archivos parquet en `data/raw`,
- convierte columnas de fecha a `datetime`,
- elimina duplicados y registros incompletos,
- filtra viajes inválidos,
- crea columnas derivadas como duración del viaje y mes,
- guarda archivos procesados en `data/processed/`,
- genera el resumen mensual en `data/results/resumen_mensual.csv`.

### 3. Carga a BigQuery
El script `scripts/04_carga_bigquery.py`:

- carga el CSV agregado a la tabla `resumen_mensual`,
- carga los archivos parquet procesados a la tabla `yellow_taxi_processed`,
- actualiza la base de datos analítica con `WRITE_TRUNCATE`.

### 4. Orquestación del pipeline
El archivo `scripts/pipeline_integration.py` ejecuta todo el proceso completo en secuencia:

1. ingestión,
2. transformación,
3. subida de archivos procesados a Storage,
4. carga a BigQuery.

## Requisitos previos

Antes de ejecutar el proyecto necesitas:

- Python 3.10 o superior
- Git
- Google Cloud SDK (`gcloud` / `gsutil`) instalado y configurado
- Una cuenta de Google Cloud con acceso a:
  - Cloud Storage
  - BigQuery
- Un bucket de GCS creado
- Un proyecto de GCP y un dataset BigQuery

## Configuración

Ajusta los nombres de los recursos en los scripts según tu entorno real:

- `ingesta_datos/ingest_data.py`
  - `BUCKET_NAME = os.environ.get("GCS_BUCKET", "nyc-taxi-datalake-grupo03")`
- `scripts/pipeline_integration.py`
  - `BUCKET = "nyc-taxi-g03-2025"`
- `scripts/04_carga_bigquery.py`
  - `PROJECT_ID = "nyc-taxi-datos-masivos-g03"`
  - `DATASET_ID = "nyc_taxi_analysis"`
  - `BUCKET_NAME = "nyc-taxi-g03-2025"`

También puedes configurar `GOOGLE_APPLICATION_CREDENTIALS` para autenticación con GCP.

## Instalación

1. Clona el repositorio:

```bash
git clone <url-del-repositorio>
cd repo-nyc-taxi-cloud-analisis-grupo03
```

2. Crea y activa un entorno virtual:

```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Instala las dependencias:

```bash
pip install -r ingesta_datos/requirements.txt
```

## Ejecución

### Ejecutar el pipeline completo

```bash
python scripts/pipeline_integration.py
```

Este comando ejecuta toda la secuencia del proyecto y deja los archivos listos en Cloud Storage y BigQuery.

### Ejecutar cada etapa por separado

#### Ingesta

```bash
python ingesta_datos/ingest_data.py
```

#### Transformación

```bash
python codigo_fuente/transformacion_datos.py
```

#### Carga a BigQuery

```bash
python scripts/04_carga_bigquery.py
```

## Resultados esperados

Al finalizar el pipeline, se generan los siguientes artefactos:

- `data/raw/`: archivos originales descargados del TLC
- `data/processed/`: archivos parquet limpios y transformados
- `data/results/resumen_mensual.csv`: resumen agregado por mes
- Bucket de GCS con carpetas `raw/`, `processed/` y `results/`
- Tablas en BigQuery:
  - `nyc_taxi_analysis.resumen_mensual`
  - `nyc_taxi_analysis.yellow_taxi_processed`

## Datos utilizados

El proyecto utiliza el dataset oficial de viajes en taxi amarillo de NYC TLC, en formato Parquet, con archivos mensuales como por ejemplo:

- `yellow_tripdata_2025-01.parquet`
- `yellow_tripdata_2025-02.parquet`
- `yellow_tripdata_2025-03.parquet`
- `yellow_tripdata_2025-04.parquet`
- `yellow_tripdata_2025-05.parquet`
- `yellow_tripdata_2025-06.parquet`

## Casos de uso

Este proyecto permite:

- análisis de demanda por mes,
- comparación de ingresos y distancias,
- evaluación de tiempos de viaje,
- creación de tableros ejecutivos,
- integración con herramientas de BI y analítica.

## Notas importantes

- La TLC publica los archivos con cierto retraso, por lo que algunos meses puede no estar disponible de inmediato.
- El bucket y el proyecto real deben ajustarse al entorno del usuario o del equipo.
- En Windows, el pipeline incluye el script `scripts/run_pipeline.bat` para facilitar la ejecución.

## Licencia

No se especifica una licencia en este repositorio. Si el proyecto va a compartirse externamente, se recomienda definir una licencia antes de publicarlo.

## Equipo

Proyecto desarrollado por el Grupo 03 para análisis de datos masivos con Google Cloud Platform.
