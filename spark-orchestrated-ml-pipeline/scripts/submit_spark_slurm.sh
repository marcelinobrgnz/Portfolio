#!/usr/bin/env bash
# Option C — university HPC / SLURM batch submit template ($0)
# Usage: sbatch scripts/submit_spark_slurm.sh wine|taxi
#SBATCH --job-name=spark-etl
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=logs/spark-etl-%j.out

set -euo pipefail

DATASET="${1:-wine}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
module load spark/3.5.0 2>/dev/null || true

if [[ "$DATASET" == "wine" ]]; then
  INPUT="$ROOT/data/raw/wine"
  OUTPUT="$ROOT/data/features/wine"
else
  INPUT="$ROOT/data/raw/taxi"
  OUTPUT="$ROOT/data/features/taxi"
fi

spark-submit \
  --master yarn \
  --deploy-mode client \
  "$ROOT/spark_jobs/transform.py" \
  --dataset "$DATASET" \
  --input "$INPUT" \
  --output "$OUTPUT" \
  --metrics-file "$OUTPUT/_metrics.json"

echo "Spark ETL complete: $OUTPUT"
