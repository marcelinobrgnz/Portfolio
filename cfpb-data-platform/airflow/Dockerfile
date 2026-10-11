FROM apache/airflow:2.9.3

USER root
RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

USER airflow
RUN pip install --no-cache-dir \
    "dbt-snowflake>=1.8,<1.10" \
    snowflake-connector-python \
    python-dotenv \
    pandas \
    pyarrow \
    boto3
