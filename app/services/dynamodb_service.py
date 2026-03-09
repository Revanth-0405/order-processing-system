import uuid
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key
from lambdas.shared.dynamo_utils import get_dynamodb_resource

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
        
        table.put_item(Item=item)
        return item

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
    def get_all_events():
        table = DynamoDBService.get_table()
        
        response = table.scan()
        return response.get('Items', [])