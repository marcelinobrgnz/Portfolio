#!/bin/bash
set -e
curl -sf -u admin:admin 'http://127.0.0.1:8080/api/v1/dags/cfpb_snowflake_dbt_pipeline/dagRuns?limit=5&order_by=-start_date' > /tmp/dag_runs.json
python3 - <<'PY'
import json
d=json.load(open('/tmp/dag_runs.json'))
for r in d.get('dag_runs',[]):
    print(r.get('dag_run_id'), r.get('state'))
PY
echo '---HEALTH---'
curl -sf -u admin:admin http://127.0.0.1:8080/health
echo
cd /mnt/d/IIMA/Portfolio/cfpb-data-platform
rid=$(python3 - <<'PY'
import json
d=json.load(open('/tmp/dag_runs.json'))
print(d['dag_runs'][0]['dag_run_id'])
PY
)
echo "latest=$rid"
docker compose -f airflow/docker-compose.yml exec -T airflow-scheduler \
  airflow tasks states-for-dag-run cfpb_snowflake_dbt_pipeline "$rid" -o table
