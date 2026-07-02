# AWS Teardown Verification

Generated: 2026-07-02T10:12:52.3207500Z UTC

## Billable compute (should all be CLEAR)

- [OK] **ECS clusters:** CLEAR - (none)
- [OK] **ECR repositories:** CLEAR - (none)
- [OK] **CloudWatch log groups:** CLEAR - (none)
- [OK] **Demo security group:** CLEAR - (none)

## S3 kept on purpose (storage only, under 2 USD/mo)

PRE data/
                           PRE drift-reports/
                           PRE mlflow-artifacts/
                           PRE models/

## Expected ongoing cost

| Resource | Monthly |
|----------|---------|
| S3 artifacts | under 2 USD |
| ECS / Fargate / ECR | 0 USD |
| SageMaker | 0 USD |

**Result: No active compute billing from this demo.**

