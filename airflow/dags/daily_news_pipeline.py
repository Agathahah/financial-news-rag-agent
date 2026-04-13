from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "agatha",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="daily_financial_news_pipeline",
    default_args=default_args,
    description="Ingest, process, and embed financial news daily",
    schedule_interval="0 7 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["financial", "nlp", "spark"],
) as dag:

    ingest = BashOperator(
        task_id="spark_ingestion",
        bash_command="cd /app && python -m src.ingestion.spark_pipeline",
    )

    analytics = BashOperator(
        task_id="spark_analytics",
        bash_command="cd /app && python -m src.analytics.spark_analytics",
    )

    embed = BashOperator(
        task_id="embed_articles",
        bash_command="cd /app && python -m src.embedding.embedder",
    )

    ingest >> analytics >> embed
