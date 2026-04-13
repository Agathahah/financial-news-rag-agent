import os
import time
from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F
from dotenv import load_dotenv

load_dotenv()

POSTGRES_URL = (
    f"jdbc:postgresql://"
    f"{os.getenv('POSTGRES_HOST', '127.0.0.1')}:"
    f"{os.getenv('POSTGRES_PORT', '5433')}/"
    f"{os.getenv('POSTGRES_DB', 'finews')}"
)
POSTGRES_PROPS = {
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres123"),
    "driver": "org.postgresql.Driver",
}

FINANCIAL_ENTITIES = [
    "Bank Indonesia", "BI rate", "IHSG",
    "rupiah", "inflasi", "OJK"
]

def create_spark():
    return (
        SparkSession.builder
        .appName("FinancialNewsAnalytics")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.driver.memory", os.getenv("SPARK_DRIVER_MEMORY", "4g"))
        .config("spark.jars.packages", "org.postgresql:postgresql:42.7.3")
        .getOrCreate()
    )

def run_analytics() -> dict:
    spark = create_spark()
    spark.sparkContext.setLogLevel("WARN")

    start = time.time()

    # Load dari PostgreSQL
    df = spark.read.jdbc(
        url=POSTGRES_URL,
        table="fact_articles",
        properties=POSTGRES_PROPS
    )

    total_articles = df.count()
    print(f"\n=== Analytics Pipeline ===")
    print(f"Total articles loaded: {total_articles}")

    # === Window function: rolling 7-day article volume per source ===
    window_7d = (
        Window
        .partitionBy("source")
        .orderBy("published_date")
        .rowsBetween(-6, 0)
    )
    df = df.withColumn(
        "rolling_7d_count",
        F.count("*").over(window_7d)
    )

    # === Entity frequency — seberapa sering tiap entitas disebut ===
    for entity in FINANCIAL_ENTITIES:
        col_name = f"mentions_{entity.replace(' ', '_').lower()}"
        df = df.withColumn(
            col_name,
            F.when(
                F.lower(F.col("title")).contains(entity.lower()), 1
            ).otherwise(0)
        )

    # === Agregasi harian ===
    entity_cols = [
        f"mentions_{e.replace(' ', '_').lower()}"
        for e in FINANCIAL_ENTITIES
    ]
    daily_trends = (
        df.groupBy("published_date")
        .agg(
            F.count("*").alias("total_articles"),
            *[F.sum(c).alias(c) for c in entity_cols]
        )
        .orderBy("published_date")
    )

    # Write ke dim_daily_trends
    (
        daily_trends.write
        .jdbc(
            url=POSTGRES_URL,
            table="dim_daily_trends",
            mode="overwrite",
            properties=POSTGRES_PROPS
        )
    )

    # === Summary stats untuk business report ===
    entity_totals = {}
    for col in entity_cols:
        total = df.agg(F.sum(col)).collect()[0][0] or 0
        entity_totals[col] = int(total)

    top_entity = max(entity_totals, key=entity_totals.get)
    elapsed = round(time.time() - start, 2)

    print(f"\n=== Entity Mention Summary ===")
    for entity, count in sorted(entity_totals.items(), key=lambda x: -x[1]):
        label = entity.replace("mentions_", "").replace("_", " ").title()
        print(f"  {label:<20}: {count} mentions")

    print(f"\nTop entity    : {top_entity.replace('mentions_', '')}")
    print(f"Days analyzed : {daily_trends.count()}")
    print(f"Processing time: {elapsed}s")

    spark.stop()

    return {
        "total_articles": total_articles,
        "entity_totals": entity_totals,
        "top_entity": top_entity,
        "elapsed_seconds": elapsed,
    }

def get_daily_trends(entity: str, days: int = 7) -> dict:
    """Dipanggil oleh LangGraph tools nanti."""
    import psycopg2
    col_name = f"mentions_{entity.replace(' ', '_').lower()}"
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=os.getenv("POSTGRES_PORT", 5433),
        dbname=os.getenv("POSTGRES_DB", "finews"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres123"),
    )
    cur = conn.cursor()
    try:
        cur.execute(
            f"""
            SELECT COALESCE(SUM({col_name}), 0) as total,
                   COUNT(*) as days
            FROM dim_daily_trends
            WHERE published_date >= CURRENT_DATE - INTERVAL '{days} days'
            """
        )
        row = cur.fetchone()
        total = int(row[0]) if row else 0
        direction = 1 if total > 2 else -1
    except Exception:
        total, direction = 0, 0
    finally:
        conn.close()

    return {"total": total, "direction": direction}

if __name__ == "__main__":
    stats = run_analytics()
    print(f"\nDone: {stats['elapsed_seconds']}s")
