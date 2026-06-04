"""
Hourly DAG: ingest "Software Engineer" jobs in Berlin, Germany into Qdrant.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

log = logging.getLogger(__name__)

JOB_TITLE = "software engineer"
COUNTRY = "germany"
LOCATION = "berlin"
JOBS_PER_RUN = 50


def _ingest_jobs(**context) -> int:
    from ingestion.ingest import run
    n = run(title=JOB_TITLE, country=COUNTRY, location=LOCATION, limit=JOBS_PER_RUN, language="en")
    log.info("Upserted %d jobs — %s / %s", n, COUNTRY, LOCATION)
    return n


with DAG(
    dag_id="ingest_software_engineer_jobs_berlin",
    description="Hourly ingestion of Software Engineer jobs in Berlin into Qdrant",
    schedule="@hourly",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["jobs", "ingestion", "berlin"],
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=3),
        "execution_timeout": timedelta(minutes=20),
    },
) as dag:
    PythonOperator(
        task_id="ingest__germany__berlin",
        python_callable=_ingest_jobs,
    )
