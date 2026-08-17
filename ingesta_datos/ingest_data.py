

import os
import sys
import logging
import requests
import pandas as pd
from datetime import datetime, timezone
from google.cloud import storage
from google.api_core.exceptions import NotFound


DATASET_FILES = [
    "yellow_tripdata_2025-01.parquet",
    "yellow_tripdata_2025-02.parquet",
    "yellow_tripdata_2025-03.parquet",
    "yellow_tripdata_2025-04.parquet",
    "yellow_tripdata_2025-05.parquet",
    "yellow_tripdata_2025-06.parquet",
]
BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"

LOCAL_DIR = "data/raw"
BUCKET_NAME = os.environ.get("GCS_BUCKET", "nyc-taxi-datalake-grupo03")  # ajustar al nombre real del bucket
RAW_PREFIX = "raw/"

# Esquema esperado según el dataset (21 variables, definidas en Entrega 1).
# (tarifa de congestión del distrito central de negocios de Manhattan).
COLUMNAS_ESPERADAS = [
    "VendorID", "tpep_pickup_datetime", "tpep_dropoff_datetime",
    "passenger_count", "trip_distance", "RatecodeID", "store_and_fwd_flag",
    "PULocationID", "DOLocationID", "payment_type", "fare_amount", "extra",
    "mta_tax", "tip_amount", "tolls_amount", "improvement_surcharge",
    "total_amount", "congestion_surcharge", "Airport_fee",
    "cbd_congestion_fee",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def descargar_dataset(nombre_archivo: str, destino_dir: str) -> str:
    """Descarga un archivo Parquet del portal oficial de TLC si no existe localmente."""
    os.makedirs(destino_dir, exist_ok=True)
    destino = os.path.join(destino_dir, nombre_archivo)
    url = f"{BASE_URL}/{nombre_archivo}"

    if os.path.exists(destino):
        log.info(f"Archivo ya existe localmente: {destino}, se omite descarga.")
        return destino

    log.info(f"Descargando {nombre_archivo} desde {url} ...")
    with requests.get(url, stream=True, timeout=120) as r:
        if r.status_code in (403, 404):
            raise FileNotFoundError(
                f"El archivo {nombre_archivo} no está disponible todavía en TLC "
                f"(HTTP {r.status_code}). La TLC publica los datos con ~2 meses "
                f"de rezago."
            )
        r.raise_for_status()
        descargado = 0
        with open(destino, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
                descargado += len(chunk)
    log.info(f"Descarga completa: {nombre_archivo} ({descargado / (1024*1024):.2f} MB)")
    return destino


def subir_a_gcs(archivo_local: str, bucket_name: str, blob_name: str) -> str:
    """Sube un archivo local al bucket de Google Cloud Storage, dentro de raw/."""
    client = storage.Client()

    try:
        bucket = client.get_bucket(bucket_name)
    except NotFound:
        log.error(
            f"El bucket '{bucket_name}' no existe. Debe crearse antes desde "
            f"la consola de GCP o con: gsutil mb -l us-east1 gs://{bucket_name}"
        )
        raise

    blob = bucket.blob(blob_name)
    log.info(f"Subiendo {archivo_local} -> gs://{bucket_name}/{blob_name}")
    blob.upload_from_filename(archivo_local, timeout=600)
    log.info("Carga a Cloud Storage completada.")
    return blob_name


def validar_almacenamiento(bucket_name: str, blob_name: str, tamano_local: int) -> bool:
    """Valida que el objeto se subió correctamente comparando tamaños y metadatos."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.get_blob(blob_name)

    if blob is None:
        log.error(f"❌ No se encontró el objeto gs://{bucket_name}/{blob_name}")
        return False

    log.info(f"Objeto encontrado en GCS: {blob_name}")
    log.info(f"Tamaño en GCS: {blob.size} bytes | Tamaño local: {tamano_local} bytes")
    log.info(f"Última modificación: {blob.updated}")
    log.info(f"MD5 hash: {blob.md5_hash}")

    if blob.size == tamano_local:
        log.info("Validación de tamaño exitosa: coinciden.")
        return True
    else:
        log.error("Los tamaños NO coinciden. Posible carga incompleta o corrupta.")
        return False


def revisar_estructura_y_consistencia(archivo_local: str) -> bool:
    """
    Tarea 8: revisa columnas, tipos de datos y valores nulos del archivo
    Parquet antes de continuar con el procesamiento (limpieza/transformación,
    que corresponde a otra parte del equipo).
    """
    log.info(f"Revisando estructura de {archivo_local} ...")
    df = pd.read_parquet(archivo_local)

    columnas_actuales = list(df.columns)
    faltantes = [c for c in COLUMNAS_ESPERADAS if c not in columnas_actuales]
    if faltantes:
        log.warning(f"Columnas esperadas ausentes en este archivo: {faltantes}")
    else:
        log.info("El archivo contiene todas las columnas base esperadas.")

    log.info(f"Número de registros: {len(df):,}")
    log.info(f"Número de columnas: {len(columnas_actuales)}")

    nulos = df.isnull().sum()
    nulos = nulos[nulos > 0]
    if not nulos.empty:
        log.info("Valores nulos detectados por columna:\n" + str(nulos))
    else:
        log.info("No se detectaron valores nulos.")

    log.info("Tipos de datos por columna:\n" + str(df.dtypes))

    return len(faltantes) == 0


def main():
    resumen = []
    omitidos = []

    for nombre_archivo in DATASET_FILES:
        log.info(f"===== Procesando {nombre_archivo} =====")

        # descarga
        try:
            ruta_local = descargar_dataset(nombre_archivo, LOCAL_DIR)
        except FileNotFoundError as e:
            log.warning(f"⚠️ Omitiendo {nombre_archivo}: {e}")
            omitidos.append(nombre_archivo)
            continue

        tamano_local = os.path.getsize(ruta_local)

        # subida a raw/
        blob_name = f"{RAW_PREFIX}{nombre_archivo}"
        subir_a_gcs(ruta_local, BUCKET_NAME, blob_name)

        # validación de la carga
        carga_ok = validar_almacenamiento(BUCKET_NAME, blob_name, tamano_local)

        # revisión de estructura y consistencia
        estructura_ok = revisar_estructura_y_consistencia(ruta_local)

        resumen.append({
            "archivo": nombre_archivo,
            "tamano_mb": round(tamano_local / (1024 * 1024), 2),
            "carga_valida": carga_ok,
            "estructura_valida": estructura_ok,
        })

    log.info("===== Resumen de ingesta =====")
    for r in resumen:
        log.info(r)
    if omitidos:
        log.warning(f"Archivos omitidos (aún no publicados por TLC): {omitidos}")

    if not resumen:
        log.error("No se pudo procesar ningún archivo. Revisar disponibilidad en TLC.")
        sys.exit(1)

    if not all(r["carga_valida"] and r["estructura_valida"] for r in resumen):
        log.error("Uno o más archivos presentaron problemas. Revisar logs.")
        sys.exit(1)

    log.info(f"Proceso de ingesta finalizado con éxito. Timestamp: {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()