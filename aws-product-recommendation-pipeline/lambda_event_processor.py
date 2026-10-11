import json
import boto3
from datetime import datetime

s3 = boto3.client('s3')
glue = boto3.client('glue')

BUCKET_NAME = 'amazon-electronics'
GLUE_JOB_NAME = 'process-new-events'

def lambda_handler(event, context):
    """
    Triggered when new files arrive in raw/stream/
    Validates and triggers Glue ETL job
    """
    records = event.get('Records', [])
    
    for record in records:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        
        # Validate file
        if not key.endswith('.parquet'):
            print(f"Skipping non-parquet file: {key}")
            continue
        
        # Trigger Glue job
        try:
            response = glue.start_job_run(
                JobName=GLUE_JOB_NAME,
                Arguments={
                    '--S3_INPUT': f's3://{bucket}/{key}',
                    '--S3_OUTPUT': f's3://{BUCKET_NAME}/processed/events/',
                    '--JOB_NAME': GLUE_JOB_NAME
                }
            )
            print(f"Started Glue job run: {response['JobRunId']}")
        except Exception as e:
            print(f"Error starting Glue job: {str(e)}")
            raise
    
    return {
        'statusCode': 200,
        'body': json.dumps('Processing triggered successfully')
    }