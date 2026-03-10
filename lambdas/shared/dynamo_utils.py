import boto3
import os
from botocore.exceptions import ClientError

def get_dynamodb_resource():
    """Returns a boto3 DynamoDB resource configured for local or AWS."""
    # We use dummy credentials for LocalStack/DynamoDB Local
    return boto3.resource(
        'dynamodb',
        endpoint_url=os.environ.get('DYNAMODB_URL', 'http://localhost:8000'),
        region_name=os.environ.get('AWS_REGION', 'us-east-1'),
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID', 'dummy'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY', 'dummy')
    )

def create_order_events_table():
    """Creates the OrderEvents table if it doesn't exist."""
    dynamodb = get_dynamodb_resource()
    
    try:
        # Define table schema as per requirements
        table = dynamodb.create_table(
            TableName='OrderEvents',
            KeySchema=[
                {'AttributeName': 'order_id', 'KeyType': 'HASH'},  # Partition key
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'} # Sort key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'order_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'},
                {'AttributeName': 'event_type', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'EventTypeIndex',
                    'KeySchema': [
                        {'AttributeName': 'event_type', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                }
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        table.wait_until_exists()
        print("Successfully created DynamoDB table: OrderEvents")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            pass # Table already exists, which is fine
        else:
            print(f"Error creating table: {e}")