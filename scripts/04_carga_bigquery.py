from google.cloud import bigquery

PROJECT_ID = "nyc-taxi-datos-masivos-g03"
DATASET_ID = "nyc_taxi_analysis"
BUCKET_NAME = "nyc-taxi-g03-2025"

RESUMEN_URI = f"gs://{BUCKET_NAME}/results/resumen_mensual.csv"
PROCESSED_URI = f"gs://{BUCKET_NAME}/processed/*.parquet"

client = bigquery.Client(project=PROJECT_ID)


def load_resumen_mensual():
    table_id = f"{PROJECT_ID}.{DATASET_ID}.resumen_mensual"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    load_job = client.load_table_from_uri(
        RESUMEN_URI,
        table_id,
        job_config=job_config,
    )

    load_job.result()
    table = client.get_table(table_id)

    print(f"Tabla cargada: {table_id}")
    print(f"Filas cargadas: {table.num_rows}")


def load_yellow_taxi_processed():
    table_id = f"{PROJECT_ID}.{DATASET_ID}.yellow_taxi_processed"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    load_job = client.load_table_from_uri(
        PROCESSED_URI,
        table_id,
        job_config=job_config,
    )

    load_job.result()
    table = client.get_table(table_id)

    print(f"Tabla cargada: {table_id}")
    print(f"Filas cargadas: {table.num_rows}")


def main():
    print("Iniciando carga de datos a BigQuery...")
    load_resumen_mensual()
    load_yellow_taxi_processed()
    print("Carga a BigQuery completada correctamente.")


if __name__ == "__main__":
    main()