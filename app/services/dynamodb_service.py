import uuid
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key
from lambdas.shared.dynamo_utils import get_dynamodb_resource
from app.services.lambda_invoker import LambdaInvoker
import logging

class DynamoDBService:
    @staticmethod
    def get_table():
        dynamodb = get_dynamodb_resource()
        return dynamodb.Table('OrderEvents')

    @staticmethod
    def put_event(order_id, event_type, payload, processed_by):
        table = DynamoDBService.get_table()
        
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        item = {
            'order_id': str(order_id),
            'timestamp': timestamp,
            'event_id': event_id,
            'event_type': event_type,
            'payload': payload,
            'processed_by': processed_by,
            'created_at': timestamp
        }
        
        try:
            table.put_item(Item=item)
            
            # Automatically trigger the webhook Lambda for every new event
            webhook_payload = {
                "order_id": str(order_id),
                "event_type": event_type,
                "payload": payload or {}
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