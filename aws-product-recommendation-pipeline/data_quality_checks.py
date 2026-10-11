import boto3
import pandas as pd
from datetime import datetime

s3 = boto3.client('s3')
BUCKET = 'amazon-electronics'

def validate_events_data(s3_path):
    """Run data quality checks on events table"""
    df = pd.read_parquet(s3_path)
    
    checks = {
        'total_records': len(df),
        'null_user_ids': df['user_id'].isnull().sum(),
        'null_item_ids': df['item_id'].isnull().sum(),
        'null_timestamps': df['timestamp'].isnull().sum(),
        'duplicate_records': df.duplicated().sum(),
        'date_range': {
            'min': df['date'].min(),
            'max': df['date'].max()
        },
        'rating_distribution': df['rating'].value_counts().to_dict()
    }
    
    # Alert if issues found
    if checks['null_user_ids'] > 0:
        print(f"WARNING: {checks['null_user_ids']} null user_ids found")
    
    if checks['null_item_ids'] > 0:
        print(f"WARNING: {checks['null_item_ids']} null item_ids found")
    
    return checks

if __name__ == '__main__':
    s3_path = f's3://{BUCKET}/processed/events/'
    results = validate_events_data(s3_path)
    print(results)