import uuid
import boto3
import logging
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key
from app.utils import logger
from lambdas.shared.dynamo_utils import get_dynamodb_resource
from app.services.lambda_invoker import LambdaInvoker
from flask import g, has_request_context


class DynamoDBService:
    @staticmethod
    def get_table():
        dynamodb = get_dynamodb_resource()
        return dynamodb.Table('OrderEvents')

    @staticmethod
    def put_event(order_id, event_type, payload=None, processed_by="system", request_id=None):
        table = DynamoDBService.get_table()
        
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        if not request_id and has_request_context() and hasattr(g, 'request_id'):
            request_id = g.request_id
        
        item = {
            'order_id': str(order_id),
            'timestamp': timestamp,
            'event_id': event_id,
            'event_type': event_type,
            'payload': payload,
            'processed_by': processed_by,
            'created_at': timestamp,
            'request_id': request_id or 'N/A'
        }
        
        try:
            table.put_item(Item=item)
            
            # Automatically trigger the webhook Lambda for every new event
            webhook_payload = {
                "order_id": str(order_id),
                "event_type": event_type,
                "payload": payload or {},
                "request_id": request_id or 'N/A'
            }
            try:
                # In a real AWS environment, DynamoDB Streams handles this asynchronously.
                LambdaInvoker.invoke('send_webhook', webhook_payload)
            except Exception as e:
                logging.getLogger(__name__).error(f"Failed to trigger webhook lambda: {e}")
        
            return item
        except ClientError as e:
            print(f"Error saving event to DynamoDB: {e.response['Error']['Message']}")
            return None


    @staticmethod
    def get_events_by_order(order_id):
        table = DynamoDBService.get_table()
        
        response = table.query(
            KeyConditionExpression=Key('order_id').eq(str(order_id))
        )
        return response.get('Items', [])

    @staticmethod
    def get_events_by_type(event_type):
        table = DynamoDBService.get_table()
        
        # This requires querying the Global Secondary Index (GSI)
        response = table.query(
            IndexName='EventTypeIndex',
            KeyConditionExpression=Key('event_type').eq(event_type)
        )
        return response.get('Items', [])
    
    @staticmethod
    def get_all_events(limit=10, exclusive_start_key=None):
        table = DynamoDBService.get_table()
        scan_kwargs = {'Limit': limit}
        
        if exclusive_start_key:
            scan_kwargs['ExclusiveStartKey'] = exclusive_start_key
            
        response = table.scan(**scan_kwargs)
        
        return {
            'items': response.get('Items', []),
            'last_evaluated_key': response.get('LastEvaluatedKey')
        }
    
    @staticmethod
    def create_webhook_deliveries_table():
        dynamodb = get_dynamodb_resource()
        try:
            table = dynamodb.create_table(
                TableName='WebhookDeliveries',
                KeySchema=[
                    {'AttributeName': 'delivery_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'delivery_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'},
                    {'AttributeName': 'webhook_id', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'WebhookIdIndex',
                        'KeySchema': [
                            {'AttributeName': 'webhook_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                    }
                ],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            table.wait_until_exists()
            print("Successfully created DynamoDB table: WebhookDeliveries")
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceInUseException':
                print(f"Error creating WebhookDeliveries table: {e}")

    @staticmethod
    def log_delivery(webhook_id, url, event_type, payload, status_code, success, attempts, error=None):
        table = get_dynamodb_resource().Table('WebhookDeliveries')

        if not request_id and has_request_context() and hasattr(g, 'request_id'):
            request_id = g.request_id
        item = {
            'delivery_id': str(uuid.uuid4()),
            'webhook_id': str(webhook_id),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'target_url': url,
            'event_type': event_type,
            'payload': payload,
            'status_code': status_code,
            'success': success,
            'attempts': attempts,
            'error': error,
            'request_id': request_id or 'N/A'
        }
        table.put_item(Item=item)
        return item
    
    @staticmethod
    def get_delivery_count_last_hour(webhook_id):
        table = DynamoDBService._get_dynamodb_resource().Table('WebhookDeliveries')
        from boto3.dynamodb.conditions import Key
        from datetime import timedelta
        
        # Calculate the timestamp for exactly one hour ago
        one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        
        try:
            # Query the GSI for items matching the webhook_id and a timestamp >= one hour ago
            response = table.query(
                IndexName='WebhookIdIndex',
                KeyConditionExpression=Key('webhook_id').eq(str(webhook_id)) & Key('timestamp').gte(one_hour_ago),
                Select='COUNT' # We only want the integer count, not the actual data payloads
            )
            return response.get('Count', 0)
        except Exception as e:
            logger.error(f"Error checking rate limit in DynamoDB: {e}")
            return 0