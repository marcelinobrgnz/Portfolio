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

## SageMaker Real-Time Inference — ATTEMPTED (endpoint not InService)

| Metric | Value |
|--------|-------|
| Endpoint name | `wine-quality-demo-ep` |
| Instance type | ml.t2.medium |
| Model artifact | `s3://mlops-inference-platform-864981752170/sagemaker/wine-sagemaker-model.tar.gz` |
| ECR repo | `864981752170.dkr.ecr.eu-west-1.amazonaws.com/portfolio-wine-sagemaker` |
| sklearn DLC | **Blocked** — account cannot pull `763104351884` SageMaker ECR images |
| BYOC CreateModel | **Succeeded** (Docker manifest v2 via buildx `oci-mediatypes=false`) |
| Endpoint status | **Failed** — `CannotStartContainerError` (`docker run <image> serve`) |
| Root cause | Windows CRLF in shell `entrypoint.sh`; fixed in repo via `wsgi.py` Python entrypoint |
| Blocker (final push) | Docker Desktop daemon unavailable on capture machine |

### Proof files

- `demo-proof/sagemaker/endpoint_describe.json`
- `demo-proof/aws-polish/sagemaker_deploy*.log`
- `demo-proof/sagemaker/teardown_log.json` (after teardown)

### Re-run when Docker is healthy

```powershell
.\scripts\aws\deploy_sagemaker_demo.ps1
# capture invoke proof, then:
.\scripts\aws\teardown_sagemaker.ps1
```

---

## Teardown verification

See `demo-proof/aws-polish/verify_teardown.log` — ECS, EMR, SageMaker endpoints, EKS all **CLEAR**. S3 artifacts retained (~<$2/mo).
