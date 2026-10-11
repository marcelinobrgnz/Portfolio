"""
Run SageMaker training for the Amazon Electronics recommender
using the SKLearn framework container and your custom training script.

Usage (from PowerShell in D:\IIMA\Amazon Reviews):

    python run_sagemaker_training.py
"""

import time
import traceback

import boto3
import sagemaker
from sagemaker.sklearn.estimator import SKLearn

AWS_REGION = "eu-west-1"
ROLE_ARN = "arn:aws:iam::864981752170:role/RecSys-SageMakerExecutionRole"

TRAIN_S3 = "s3://amazon-electronics/training/"
VAL_S3 = "s3://amazon-electronics/validation/"
BASE_JOB_NAME = "recsys-sklearn-best"


def main():
    print("=== Step 1: Setting up SageMaker session ===")
    boto_sess = boto3.Session(region_name=AWS_REGION)
    sm_session = sagemaker.Session(boto_session=boto_sess)
    print(f"Region: {AWS_REGION}")
    print(f"SageMaker default bucket: {sm_session.default_bucket()}")
    print()

    print("=== Step 2: Creating SKLearn estimator with best hyperparameters ===")
    estimator = SKLearn(
        entry_point="sagemaker_train_recommender.py",
        source_dir="training_code",
        role=ROLE_ARN,
        instance_type="ml.m5.2xlarge",
        instance_count=1,
        framework_version="1.2-1",
        py_version="py3",
        base_job_name=BASE_JOB_NAME,
        hyperparameters={
            # Locked-in best hyperparameters from HPO
            "max-depth": 7,
            "eta": 0.19438629701607946,
            "num-round": 131,
        },
        sagemaker_session=sm_session,
    )
    print("Estimator created.")
    print(f"  Role:    {ROLE_ARN}")
    print(f"  Train S3: {TRAIN_S3}")
    print(f"  Val S3:   {VAL_S3}")
    print()

    print("=== Step 3: Submitting single best-config training job to SageMaker ===")
    try:
        print("Submitting training job (this API call can take a few seconds)...")
        estimator.fit(
            inputs={
                "training": TRAIN_S3,
                "validation": VAL_S3,
            },
            wait=False,
            logs="None",
        )
        print("Training job submission call returned.")
    except Exception:
        print("!! Error while submitting training job:")
        traceback.print_exc()
        return

    job = estimator.latest_training_job
    if job is None:
        print("!! No training job was created (latest_training_job is None).")
        return

    job_name = job.name
    print(f"Training job submitted: {job_name}")
    print("You can also view it in AWS Console → SageMaker AI → Training jobs.")
    print()

    print("=== Step 4: Polling training job status ===")
    sm_client = boto_sess.client("sagemaker", region_name=AWS_REGION)

    terminal_states = {"Completed", "Failed", "Stopped"}
    while True:
        desc = sm_client.describe_training_job(TrainingJobName=job_name)
        status = desc["TrainingJobStatus"]
        sec = desc.get("TrainingTimeInSeconds", 0)
        print(
            f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
            f"Status: {status}, TrainingTimeInSeconds: {sec}"
        )
        if status in terminal_states:
            break
        time.sleep(30)

    print()
    print("=== Step 5: Final status ===")
    if status == "Completed":
        print(f"Training job {job_name} COMPLETED successfully.")
        print(f"Model artifacts S3 path: {desc['ModelArtifacts']['S3ModelArtifacts']}")
    else:
        print(f"Training job {job_name} ended with status: {status}")
        print("Failure reason:", desc.get("FailureReason", "(none reported)"))

    print("Done.")


if __name__ == "__main__":
    main()