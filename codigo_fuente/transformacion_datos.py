import os
import pandas as pd

# ============================================================
# CONFIGURACIÓN
# ============================================================

CARPETA_RAW = "data/raw"
CARPETA_PROCESADA = "data/processed"
CARPETA_RESULTADOS = "data/results"

os.makedirs(CARPETA_PROCESADA, exist_ok=True)
os.makedirs(CARPETA_RESULTADOS, exist_ok=True)


# ============================================================
# ARCHIVOS A PROCESAR
# ============================================================

ARCHIVOS = [
    "yellow_tripdata_2025-01.parquet",
    "yellow_tripdata_2025-02.parquet",
    "yellow_tripdata_2025-03.parquet",
    "yellow_tripdata_2025-04.parquet",
    "yellow_tripdata_2025-05.parquet",
    "yellow_tripdata_2025-06.parquet",
]


# ============================================================
# TRANSFORMACIÓN DE DATOS
# ============================================================

resumen_mensual = []

for archivo in ARCHIVOS:

    ruta_entrada = os.path.join(CARPETA_RAW, archivo)

    print(f"\nProcesando: {archivo}")

    # --------------------------------------------------------
    # 1. CARGA
    # --------------------------------------------------------

    df = pd.read_parquet(ruta_entrada)

    registros_originales = len(df)

    print(f"Registros originales: {registros_originales:,}")


    # --------------------------------------------------------
    # 2. LIMPIEZA
    # --------------------------------------------------------

    # Convertir las fechas al formato datetime
    df["tpep_pickup_datetime"] = pd.to_datetime(
        df["tpep_pickup_datetime"],
        errors="coerce"
    )

    df["tpep_dropoff_datetime"] = pd.to_datetime(
        df["tpep_dropoff_datetime"],
        errors="coerce"
    )

    # Eliminar registros duplicados
    df = df.drop_duplicates()

    # Eliminar registros con valores esenciales nulos
    columnas_importantes = [
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "passenger_count",
        "trip_distance",
        "PULocationID",
        "DOLocationID",
        "total_amount"
    ]

    df = df.dropna(subset=columnas_importantes)


    # --------------------------------------------------------
    # 3. FILTRADO
    # --------------------------------------------------------

    # Conservar viajes válidos:
    # - al menos un pasajero
    # - distancia mayor que cero
    # - monto total mayor que cero
    # - fecha de recogida anterior a la de entrega

    df = df[
        (df["passenger_count"] > 0) &
        (df["trip_distance"] > 0) &
        (df["total_amount"] > 0) &
        (df["tpep_dropoff_datetime"] >= df["tpep_pickup_datetime"])
    ].copy()


    # --------------------------------------------------------
    # 4. FILTRAR POR EL MES CORRESPONDIENTE
    # --------------------------------------------------------

    # Obtener el año y mes directamente del nombre del archivo.
    # Ejemplo:
    # yellow_tripdata_2025-01.parquet -> 2025-01

    mes_archivo = archivo.replace(
        "yellow_tripdata_", ""
    ).replace(
        ".parquet", ""
    )

    # Mantener únicamente los registros que pertenecen
    # al mes correspondiente al archivo.
    df = df[
        df["tpep_pickup_datetime"].dt.strftime("%Y-%m") == mes_archivo
    ].copy()

    registros_filtrados = len(df)

    print(
        f"Registros después de limpieza y filtrado: "
        f"{registros_filtrados:,}"
    )


    # --------------------------------------------------------
    # 5. CREAR VARIABLES PARA EL ANÁLISIS
    # --------------------------------------------------------

    df["mes"] = (
        df["tpep_pickup_datetime"]
        .dt.to_period("M")
        .astype(str)
    )

    # Calcular duración del viaje en minutos
    df["duracion_minutos"] = (
        df["tpep_dropoff_datetime"]
        - df["tpep_pickup_datetime"]
    ).dt.total_seconds() / 60

    # Eliminar duraciones negativas o iguales a cero
    df = df[df["duracion_minutos"] > 0].copy()


    # --------------------------------------------------------
    # 6. GUARDAR DATOS TRANSFORMADOS
    # --------------------------------------------------------

    nombre_salida = archivo.replace(
        ".parquet",
        "_processed.parquet"
    )

    ruta_salida = os.path.join(
        CARPETA_PROCESADA,
        nombre_salida
    )

    df.to_parquet(
        ruta_salida,
        index=False
    )

    print(
        f"Archivo procesado guardado: "
        f"{ruta_salida}"
    )


    # --------------------------------------------------------
    # 7. AGREGACIÓN
    # --------------------------------------------------------

    agregado = (
        df.groupby("mes")
        .agg(
            total_viajes=("VendorID", "count"),
            pasajeros_promedio=("passenger_count", "mean"),
            distancia_promedio=("trip_distance", "mean"),
            ingreso_promedio=("total_amount", "mean"),
            ingreso_total=("total_amount", "sum"),
            duracion_promedio_minutos=("duracion_minutos", "mean")
        )
        .reset_index()
    )

    resumen_mensual.append(agregado)


# ============================================================
# UNIR LOS RESULTADOS DE LOS 6 MESES
# ============================================================

resultado_final = pd.concat(
    resumen_mensual,
    ignore_index=True
)

resultado_final = resultado_final.sort_values("mes")


# ============================================================
# GUARDAR RESULTADO DE LA AGREGACIÓN
# ============================================================

ruta_resultado = os.path.join(
    CARPETA_RESULTADOS,
    "resumen_mensual.csv"
)

resultado_final.to_csv(
    ruta_resultado,
    index=False
)


# ============================================================
# RESULTADO FINAL
# ============================================================

print("\n========================================")
print("TRANSFORMACIÓN COMPLETADA")
print("========================================")

print("\nResumen mensual:")
print(resultado_final)

print(
    f"\nResultado guardado en: "
    f"{ruta_resultado}"
)