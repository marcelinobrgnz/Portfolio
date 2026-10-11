#!/bin/bash
set -e
pgrep dockerd >/dev/null || { dockerd >/var/log/dockerd.log 2>&1 & sleep 5; }
cd /mnt/d/IIMA/Portfolio/cfpb-data-platform
export CFPB_SKIP_INGEST=1
docker start airflow-postgres-1 || true
sleep 3
docker compose -f airflow/docker-compose.yml up -d
echo WAIT_HEALTH
for i in $(seq 1 40); do
  if curl -sf http://127.0.0.1:8080/health >/tmp/af_health.json; then
    echo HEALTH_OK
    cat /tmp/af_health.json
    echo
    docker compose -f airflow/docker-compose.yml ps
    exit 0
  fi
  echo "wait_$i"
  sleep 10
done
echo HEALTH_FAIL
docker compose -f airflow/docker-compose.yml ps
docker compose -f airflow/docker-compose.yml logs --tail 40 airflow-webserver
exit 1
