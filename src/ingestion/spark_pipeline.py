import os
import time
from pyspark.sql import SparkSession
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

def create_spark():
    return (
        SparkSession.builder
        .appName("FinancialNewsPipeline")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.driver.memory", os.getenv("SPARK_DRIVER_MEMORY", "4g"))
        .config(
            "spark.jars.packages",
            "org.postgresql:postgresql:42.7.3"
        )
        .getOrCreate()
    )

def run_ingestion_pipeline(raw_articles: list) -> dict:
    spark = create_spark()
    spark.sparkContext.setLogLevel("WARN")

    start = time.time()
    df = spark.createDataFrame(raw_articles)
    initial_count = df.count()

    # Deduplicate by URL
    df = df.dropDuplicates(["url"])

    # Normalize timestamp
    df = df.withColumn(
        "published_date",
        F.to_date(F.col("published_at")).cast("date")
    )

    # Quality filter
    df = df.filter(
        F.col("title").isNotNull() &
        (F.length(F.col("title")) > 10)
    )

    final_count = df.count()
    elapsed = round(time.time() - start, 2)

    # Log stats
    print(f"\n=== Ingestion Pipeline Stats ===")
    print(f"Raw articles    : {initial_count}")
    print(f"After dedup     : {final_count}")
    print(f"Duplicates removed: {initial_count - final_count}")
    print(f"Processing time : {elapsed}s")

    # Write ke PostgreSQL
    (
        df.select("source", "title", "url", "summary", "published_date", "language")
        .write
        .jdbc(url=POSTGRES_URL, table="fact_articles", mode="append", properties=POSTGRES_PROPS)
    )
    print(f"Written {final_count} articles to PostgreSQL")
    spark.stop()

    return {
        "initial_count": initial_count,
        "final_count": final_count,
        "duplicates_removed": initial_count - final_count,
        "elapsed_seconds": elapsed,
    }

if __name__ == "__main__":
    from src.ingestion.fetch_news import load_sample_articles
    articles = load_sample_articles()
    stats = run_ingestion_pipeline(articles)
    print(f"\nDone: {stats}")
