#!/bin/bash
set -e
cd /mnt/d/IIMA/Portfolio/cfpb-data-platform
# ensure unix line endings on .env for `source`
sed -i 's/\r$//' .env || true
docker compose -f airflow/docker-compose.yml exec -T airflow-scheduler \
  airflow dags reserialize || true
docker compose -f airflow/docker-compose.yml exec -T airflow-scheduler \
  airflow dags unpause cfpb_snowflake_dbt_pipeline || true
docker compose -f airflow/docker-compose.yml exec -T airflow-scheduler \
  airflow dags trigger cfpb_snowflake_dbt_pipeline
echo TRIGGERED
for i in $(seq 1 90); do
  out=$(docker compose -f airflow/docker-compose.yml exec -T airflow-scheduler \
    airflow dags list-runs -d cfpb_snowflake_dbt_pipeline -o plain 2>/dev/null | head -5)
  state=$(echo "$out" | awk 'NR==2{print $NF}')
  echo "poll_$i state=$state"
  if [ "$state" = "success" ]; then
    echo DAG_SUCCESS
    echo "$out"
    exit 0
  fi
  if [ "$state" = "failed" ]; then
    echo DAG_FAILED
    run_id=$(echo "$out" | awk 'NR==2{print $2}')
    docker compose -f airflow/docker-compose.yml exec -T airflow-scheduler \
      airflow tasks states-for-dag-run cfpb_snowflake_dbt_pipeline "$run_id" -o table || true
    exit 1
  fi
  sleep 20
done
echo DAG_TIMEOUT
exit 1
