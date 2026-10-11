#!/bin/bash
set -e
for i in $(seq 1 60); do
  curl -sf -u admin:admin 'http://127.0.0.1:8080/api/v1/dags/cfpb_snowflake_dbt_pipeline/dagRuns?limit=1&order_by=-start_date' > /tmp/dag_runs.json
  state=$(python3 -c "import json; print(json.load(open('/tmp/dag_runs.json'))['dag_runs'][0]['state'])")
  rid=$(python3 -c "import json; print(json.load(open('/tmp/dag_runs.json'))['dag_runs'][0]['dag_run_id'])")
  echo "poll_$i $rid $state"
  if [ "$state" = "success" ]; then
    echo DAG_SUCCESS
    curl -sf -u admin:admin "http://127.0.0.1:8080/api/v1/dags/cfpb_snowflake_dbt_pipeline/dagRuns/$rid/taskInstances" > /mnt/d/IIMA/Portfolio/cfpb-data-platform/docs/snapshots_private/H_airflow_task_instances.json
    cp /tmp/dag_runs.json /mnt/d/IIMA/Portfolio/cfpb-data-platform/docs/snapshots_private/H_airflow_dag_runs.json
    exit 0
  fi
  if [ "$state" = "failed" ]; then
    echo DAG_FAILED
    curl -sf -u admin:admin "http://127.0.0.1:8080/api/v1/dags/cfpb_snowflake_dbt_pipeline/dagRuns/$rid/taskInstances" > /mnt/d/IIMA/Portfolio/cfpb-data-platform/docs/snapshots_private/H_airflow_task_instances.json
    exit 1
  fi
  sleep 20
done
echo DAG_TIMEOUT
exit 1
