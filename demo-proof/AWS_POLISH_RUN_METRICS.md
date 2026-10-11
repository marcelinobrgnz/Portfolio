# AWS Polish Run — EMR Success + SageMaker Attempts (2026-07-02)

> Region: **eu-west-1** | Account: **864981752170** | All compute torn down after capture.

## EMR Serverless Spark — SUCCESS

| Metric | Value |
|--------|-------|
| Application | `portfolio-spark-demo` (`00g6ti26amk2al0p`) |
| Job run | `00g6tjkq9nrmm80r` |
| State | **SUCCESS** |
| Release | emr-7.0.0 |
| Role | `EMRServerlessWineDemoRole` |
| Wall-clock (script) | ~184 s |
| Input | `s3://mlops-inference-platform-864981752170/emr-demo/input/wine/` |
| Output | `s3://mlops-inference-platform-864981752170/emr-demo/output/wine/` |
| Partitions | 2 (`wine_type=0`, `wine_type=1`) |
| Output files | `_SUCCESS`, 2 snappy Parquet parts (~191 KB total) |
| Wine rows (source) | **6,497** (UCI red + white CSVs) |

### Fixes applied for success

1. Removed `--master yarn` from job args (EMR Serverless sets cluster manager).
2. Added `spark.hadoop.fs.s3a.endpoint.region=eu-west-1` (was defaulting to us-east-1).
3. `helpers_pkg.zip` py-files + import fallback in `transform.py`.

### Proof files

- `demo-proof/emr-serverless/job_run_describe.json`
- `demo-proof/emr-serverless/emr_metrics.json`
- `demo-proof/emr-serverless/s3_output_listing.txt`
- `demo-proof/emr-serverless/job_driver.json`

---

## SageMaker Real-Time Inference — SUCCESS (2026-07-03)

| Metric | Value |
|--------|-------|
| Endpoint | `wine-quality-demo-ep` |
| Instance | ml.t2.medium |
| Image build | **AWS CodeBuild** (no local Docker) |
| Endpoint status | **InService** |
| Invoke latency | ~2.3 s (first invoke) |
| Prediction | `{"predictions": [0]}` |
| Deploy wall-clock | ~302 s |
| Proof | `demo-proof/sagemaker/invoke_response.json`, `sagemaker_metrics.json` |
| Teardown | `teardown_sagemaker_aws.ps1` — complete |

### Re-run

```powershell
.\scripts\aws\deploy_sagemaker_aws.ps1
.\scripts\aws\teardown_sagemaker_aws.ps1
```

---

## Teardown verification

See `demo-proof/aws-polish/verify_teardown.log` — ECS, EMR, SageMaker endpoints, EKS all **CLEAR**. S3 artifacts retained (~<$2/mo).
