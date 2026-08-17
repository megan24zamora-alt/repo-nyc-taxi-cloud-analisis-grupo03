import platform
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent

INGEST_SCRIPT = ROOT_DIR / "ingesta_datos" / "ingest_data.py"
TRANSFORM_SCRIPT = ROOT_DIR / "codigo_fuente" / "transformacion_datos.py"
BIGQUERY_SCRIPT = ROOT_DIR / "scripts" / "04_carga_bigquery.py"

BUCKET = "nyc-taxi-g03-2025"


def run_python_script(script_path: Path, step_name: str):
    print(f"\n===== {step_name} =====")

    if not script_path.exists():
        raise FileNotFoundError(f"No se encontró el script: {script_path}")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(ROOT_DIR),
    )

    if result.returncode != 0:
        raise RuntimeError(f"Falló la etapa: {step_name}")


def run_command(command: list[str], step_name: str):
    print(f"\n===== {step_name} =====")

    result = subprocess.run(
        command,
        cwd=str(ROOT_DIR),
        shell=False,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Falló la etapa: {step_name}")


def get_gsutil_command():
    return "gsutil.cmd" if platform.system() == "Windows" else "gsutil"


def upload_processed_to_cloud_storage():
    gsutil = get_gsutil_command()

    run_command(
        [
            gsutil,
            "-m",
            "cp",
            "data/processed/*.parquet",
            f"gs://{BUCKET}/processed/",
        ],
        "Subida de archivos procesados a Cloud Storage",
    )

    run_command(
        [
            gsutil,
            "cp",
            "data/results/resumen_mensual.csv",
            f"gs://{BUCKET}/results/resumen_mensual.csv",
        ],
        "Subida de resultados agregados a Cloud Storage",
    )


def main():
    print("INICIANDO PIPELINE DE INTEGRACIÓN")
    print("Flujo: Input → Storage → Processing → Database → Visualization")

    run_python_script(INGEST_SCRIPT, "Ingesta y validación del dataset")
    run_python_script(TRANSFORM_SCRIPT, "Limpieza, filtrado, transformación y agregación")
    upload_processed_to_cloud_storage()
    run_python_script(BIGQUERY_SCRIPT, "Carga de datos procesados a BigQuery")

    print("\nPIPELINE FINALIZADO CORRECTAMENTE")
    print("Datos disponibles en:")
    print(f"- Cloud Storage: gs://{BUCKET}/raw/")
    print(f"- Cloud Storage: gs://{BUCKET}/processed/")
    print(f"- Cloud Storage: gs://{BUCKET}/results/")
    print("- BigQuery: nyc_taxi_analysis.resumen_mensual")
    print("- BigQuery: nyc_taxi_analysis.yellow_taxi_processed")
    print("\nLa información queda lista para análisis y visualización en Power BI.")


if __name__ == "__main__":
    main()